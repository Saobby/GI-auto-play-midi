import os
import midi_api

for a, b, c in os.walk("./midi"):
    for d in c:
        path = a + "/" + d
        try:
            midi = midi_api.GIMidi(path)
        except:
            print("无法转换: {}".format(d))
            continue
        script = midi.to_keyboard_spirit_script()
        with open("./script/{}.txt".format(d), "w", encoding="utf-8") as f:
            f.write(script)
        print("已转换: {}".format(d))
