# Python工具集
> 本仓库基本为AI生成代码，结合人工BUG修复，代码微调所完成，介意勿用
> 
> 本仓库脚本不做售后，有问题可以提issue，不保证会修
> 
> 个人博客 https://jzverse.com.cn/ 还在编码中，完全开源，完全自主设计，前后端完全自研，前端采用Nuxt.js全家桶，后端采用C#最新预览版自研框架，敬请期待

## 重复文件检查
duplicate_checker脚本可以检测目录下是否有重复文件，分为精确检测和模糊检测，检测完，如果有重复文件，会生成一个结果文件，可据此来清理

## 视频批量下载
script为下载B站和油管视频的脚本，支持以下格式：
 - https://www.youtube.com/playlist?list=PLXNFA1EysfYm7qErsAy9DultSETRNFhhI
 - https://www.bilibili.com/bangumi/play/ss44152
 - https://www.bilibili.com/video/BV1CAxaeHEeH
 - https://space.bilibili.com/66607740/lists/252706
 - https://space.bilibili.com/4008741/favlist?fid=806593541&ftype=create&ctype=21
 - https://space.bilibili.com/4008741/favlist?fid=137551&ftype=collect&ctype=21
 - https://www.bilibili.com/cheese/play/ss753177039

支持配置文件，配置项如下：
```yaml
ytb_path: "C:\\App\\Portable\\YouTube-dl\\yt-dlp.exe"
download_path: "D:\\Files\\zth\\Videos\\yt-dlp"
bilibili_cookies_path: "D:\\Files\\zth\\Desktop\\www.bilibili.com_cookies.txt"
youtube_cookies_path: "D:\\Files\\zth\\Desktop\\www.youtube.com_cookies.txt"
```
配置文件名称为config.yml，参照yaml格式

cookies文件为 Netscape Cookie 格式，例如：
```txt
.youtube.com	TRUE	/	FALSE	0	PREF	tz=UTC&f6=40000000&f5=30000&f7=100&hl=en
```
下载也支持txt文件，文件格式为每行一个链接，链接后用空格隔开保存路径，会自动在保存路径下用获取到的标题作为文件夹名保存
例如：
```txt
https://space.bilibili.com/4008741/favlist?fid=4941246&ftype=collect&ctype=21 D:\Files\zth\Videos\yt-dlp\bilibili
```
下载结果会保存在result结尾的txt文件内，记事本即可打开

下载完成的，会添加✅前缀，如果具有此前缀，会跳过不下载，且下载完成也会检查文件是否完整，完整才会标记为已下载

如果有错误，会在下一行显示错误信息