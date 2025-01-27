import mido
import io

# =========================================================================
# README
# 不要在意代码中的“SC”，这个程序原本是MIDI转SC的(https://www.saobby.com/midi2scratch/)，我把它修改成MIDI转按键精灵，懒得删掉SC的了
# =========================================================================

BASE_BPM = 120
KEYS = {72: "Q", 74: "W", 76: "E", 77: "R", 79: "T", 81: "Y", 83: "U",
        60: "A", 62: "S", 64: "D", 65: "F", 67: "G", 69: "H", 71: "J",
        48: "Z", 50: "X", 52: "C", 53: "V", 55: "B", 57: "N", 59: "M"}


class _GIMidiChannel:
    def __init__(self):
        self._channel = {}

    def _create_channel(self, channel: int):
        if channel not in self._channel:
            self._channel[channel] = {"instrument": 0, "pedal": False, "volume": 127}

    def set_instrument(self, channel: int, instrument: int):
        if channel not in self._channel:
            self._create_channel(channel)
        self._channel[channel]["instrument"] = instrument

    def get_instrument(self, channel: int):
        if channel not in self._channel:
            self._create_channel(channel)
        return self._channel[channel]["instrument"]

    def set_pedal(self, channel: int, is_on: bool):
        if channel not in self._channel:
            self._create_channel(channel)
        self._channel[channel]["pedal"] = is_on

    def get_pedal(self, channel: int):
        if channel not in self._channel:
            self._create_channel(channel)
        return self._channel[channel]["pedal"]

    def set_volume(self, channel: int, volume: int):
        if channel not in self._channel:
            self._create_channel(channel)
        self._channel[channel]["volume"] = volume

    def get_volume(self, channel: int):
        if channel not in self._channel:
            self._create_channel(channel)
        return self._channel[channel]["volume"]

    def reset(self, channel: int):
        if channel not in self._channel:
            self._create_channel(channel)
        instrument = self.get_instrument(channel)
        del self._channel[channel]
        self._create_channel(channel)
        self.set_instrument(channel, instrument)

    def get_actual_volume(self, channel: int, velocity: int):
        return velocity * (self.get_volume(channel) / 127) / 127 * 100


class GIMidi:
    def __init__(self, file):
        self.playlist = []
        if isinstance(file, str):
            self._mido_obj = mido.MidiFile(filename=file)
        elif isinstance(file, bytes):
            self._mido_obj = mido.MidiFile(file=io.BytesIO(file))
        else:
            raise RuntimeError("无效的类型")
        # 合并音轨
        actions = []
        for track in self._mido_obj.tracks:
            t = 0
            for action in track:
                t += action.time
                if action.type in ["set_tempo", "program_change", "control_change", "note_on", "note_off"]:
                    actions.append((t, action))
        actions.sort(key=lambda e: e[0])
        # 处理速度变化，把改变的速度换成等效的BPM ${BASE_BPM}下的速度
        actions_new = []
        last_bpm = BASE_BPM
        t = 0
        index = 0
        for action in actions:
            if index == 0:
                delta_t = action[0]
            else:
                delta_t = action[0] - actions[index-1][0]
            t += delta_t * BASE_BPM / last_bpm
            if action[1].type == "set_tempo":
                last_bpm = mido.tempo2bpm(action[1].tempo)
            else:
                actions_new.append((t, action[1]))
            index += 1
        actions = actions_new
        del actions_new
        # 生成给sc识别的播放序列
        channels = _GIMidiChannel()
        wait = 0
        index = 0
        actions_new = []
        for action in actions:
            if index == 0:
                delta_t = action[0]
            else:
                delta_t = action[0] - actions[index-1][0]
            wait += delta_t
            if action[1].type == "program_change":
                channels.set_instrument(action[1].channel, action[1].program)
            elif action[1].type == "control_change":
                if action[1].control == 64:  # 延音
                    channels.set_pedal(action[1].channel, action[1].value >= 64)
                elif action[1].control == 7:  # 音量
                    channels.set_volume(action[1].channel, action[1].value)
                elif action[1].control == 121:  # 重置
                    channels.reset(action[1].channel)
            elif action[1].type == "note_on" and action[1].velocity > 0:
                if wait > 0:
                    actions_new.append(("wait", self._tick2beat(wait)))
                    wait = 0
                # 寻找按键弹起指令
                duration1 = 0
                for i in range(index + 1, len(actions)):
                    duration1 = actions[i][0] - action[0]
                    if (actions[i][1].type == "note_off" and actions[i][1].channel == action[1].channel and
                        actions[i][1].note == action[1].note) \
                            or (actions[i][1].type == "note_on" and actions[i][1].channel == action[1].channel and
                                actions[i][1].note == action[1].note and actions[i][1].velocity == 0):
                        break
                if channels.get_pedal(action[1].channel):  # 判断踏板是否被踩下 (这是SC的，螈神琴唔长音，不用管)
                    # 寻找松开踏板指令
                    duration0 = 0
                    for i in range(index+1, len(actions)):
                        duration0 = actions[i][0] - action[0]
                        if actions[i][1].type == "control_change" and actions[i][1].channel == action[1].channel \
                                and actions[i][1].value <= 63:
                            break
                    duration = max(duration0, duration1)  # 松开踏板和松开按键，哪个在后面就取哪个
                else:
                    duration = duration1

                beats = self._tick2beat(duration)
                inst = self._get_actual_instrument(channels, action)
                volu = channels.get_actual_volume(action[1].channel, action[1].velocity)
                # 格式: 音符_拍数_音量_乐器
                # bpm120下12拍以上之后就没声音了，所以超过12拍的时值是没意义的，但却要占用worker (这是SC的，螈神琴唔长音，不用管)
                if inst >= 200:  # 打击乐
                    actions_new.append(("beat", inst-200, beats if beats < 8 else 8, volu))
                elif inst >= 0:  # 普通乐器
                    actions_new.append(("play", action[1].note, beats if beats < 12 else 12, volu, inst))
            index += 1
        self.playlist = actions_new

    def __len__(self):
        return len(self.playlist)

    def _tick2beat(self, tick):
        return tick / self._mido_obj.ticks_per_beat

    def _get_actual_instrument(self, channels: _GIMidiChannel, action: tuple):
        if action[1].channel == 9:
            inst = action[1].note+200
        else:
            inst = channels.get_instrument(action[1].channel)
        if inst is None:
            return 0
        return inst

    def to_keyboard_spirit_script(self, allowing_instruments: list[int] = None):
        # allowing_instruments: 允许演奏的乐器ID列表
        if allowing_instruments is None:
            allowing_instruments = [i for i in range(128)]  # 默认允许所有乐器演奏
        # 自动转调: 命中键盘的音符最多的版本被认为是正确的转调
        max_hit = 0
        best_add = 0
        for add in range(-12, 13, 1):  # 尝试区间: 高低两个八度
            hit_count = 0
            for action in self.playlist:
                if action[0] == "play":
                    if action[1] + add in KEYS:
                        hit_count += 1
            if hit_count > max_hit:
                max_hit = hit_count
                best_add = add
        script = ""
        total_wait = 0
        for action in self.playlist:
            if action[0] == "wait":
                total_wait += action[1]
            elif action[0] == "play":
                if action[1] + best_add in KEYS and action[4] in allowing_instruments:  # 丢弃未命中键盘的音符和不允许演奏的乐器
                    if total_wait > 0:
                        script += "Delay {}\n".format(total_wait * (60 / BASE_BPM) * 1000)
                        total_wait = 0
                    script += 'KeyDown "{}", 1\n'.format(KEYS[action[1] + best_add])
                    script += 'KeyUp "{}", 1\n'.format(KEYS[action[1] + best_add])
            else:
                pass  # 丢弃打击乐
        return script
