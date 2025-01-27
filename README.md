# GI-auto-play-midi
 将midi文件转换为按键精灵脚本,实现在动漫游戏中自动演奏
- - - - -
# 使用方法
1. 在项目根目录执行指令:  
```
pip install -r requirements.txt
```
2. 将要转换的 midi 文件放入`./midi`文件夹
3. 运行`./main.py`
4. 生成的按键精灵脚本会被放在`./script`目录，打开希望演奏的 midi 的脚本
5. 打开按键精灵，点`新建脚本`，点击代码输入框顶部的`源文件`，将生成的脚本复制粘贴进去，点击最顶部的`保存退出`。点击左边栏的`我的脚本`找到刚刚创建的脚本，勾选它，取消勾选其它脚本。  
![image](https://github.com/user-attachments/assets/69915f4f-abe0-429f-b45d-3d424a310541)  
![image](https://github.com/user-attachments/assets/5d80dc2e-274b-4fbf-9a89-54dd330bf17e)  
![image](https://github.com/user-attachments/assets/45525504-f0e4-4b7c-88a5-1dcbfc32c8ba)
6. 打开游戏客户端，打开琴，按`F10`执行脚本
# 常见问题
1. 无法转换  
可能是 midi 文件的问题，请尝试用一些 midi 编辑器(如 MuseScore)打开要转换的 midi 文件，如果可以正常打开，用 midi 编辑器重新导出 midi ，用导出的 midi 尝试转换。如果 midi 编辑器无法打开，请更换 midi 文件。
