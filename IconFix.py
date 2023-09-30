import os
from requests import get
import re
#初始化
dir_dict={}

#爬取名字
headers={'User-Agnet':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.41"}

# 获取文件夹中的所有文件名
def get_file_list(folder_path,type):
    if type == 'ico':
        ico_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.ico'):
                    ico_files.append(os.path.join(root, file))
            for dir in dirs:
                ico_files += get_file_list(dir, 'ico')
        return ico_files
    file_list = os.listdir(folder_path)
    files = [file_name for file_name in file_list if file_name.endswith('.'+type)]
    #将文件名按照长度顺序排序
    files.sort(key=lambda x:len(x))
    return files


# 添加图标
def add_icon(file_name,folder_path):
    if file_name == '0':
        return
    # 打开文件并读取内容
    with open(os.path.join(folder_path, file_name), 'r') as file:
        content = file.read()
    pattern=r'URL=steam://rungameid/(.*)'
    id=re.findall(pattern,content)
    pattern = re.compile(r'IconFile=(.*\\(.*\.ico))')
    icon_path = pattern.search(content)
    if icon_path:
        icon_name = icon_path.group(2)
    else:
        print('未找到图标路径')
        os.system('pause')
        os._exit(1)
    url=r'https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/'
    url+=id[0]
    url+='//'+icon_name
    ico=get(url,headers=headers)
    if ico.status_code!=200:
        print('{0:<30}'.format(file_name)+'图标下载失败')
        return 
    icon_path=icon_path.group(1)
    try:
        with open(icon_path, 'wb') as file:
            file.write(ico.content)
    except PermissionError:
        print('{0:<30}'.format(file_name)+'Permission Denied')
        print('\n请关闭文件后，右键管理员权限再次运行程序\n')
        os.system('pause')
        os._exit(1)
    print('{0:<30}'.format(file_name)+'已修复')
def main():
    # 获取文件
    folder_path = os.getcwd()
    public_path=r'C:\Users\Public\Desktop'
    print('当前文件夹为：'+folder_path)
    url_files = get_file_list(folder_path,'url')
    count=len(url_files)
    url_files+= get_file_list(public_path,'url')
    #选择需要修改的文件
    print('找到'+str(len(url_files))+'个Steam快捷方式')
    print('0'+':全部')
    for i in range(len(url_files)):
        print('{:<30}'.format(str(i+1)+':'+url_files[i]),end='')
        if (i+1)%3==0:
            print('\n',end='')
    print('\n请选择需要修改的文件(用空格隔开)：')
    num_list=list(map(int,input().split()))
    if 0 not in num_list:
        for i in range(len(url_files)):
            if i+1 not in num_list:
                url_files[i]='0'
    # 修复图标
    print('单个文件修复时间小于1秒，若时间过长请科学上网，或耐心等候')
    print('开始修复图标...\n')
    i=0
    while i < count:
        add_icon(url_files[i],folder_path)
        i+=1
    print('当前文件夹已修复完成，尝试修复公共桌面快捷方式图标...')
    while i < len(url_files):
        add_icon(url_files[i],public_path)
        i+=1

    print('\n如遇问题，请联系作者\n')
    print(r'Github:https://github.com/Einck0/IconFix')
    os.system('pause')

if __name__ == "__main__":
    main()