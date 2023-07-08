import os
import string
from requests import get
import re
#初始化
alphabet_upper = string.ascii_uppercase
dir_dict={}
#获取Steam安装目录
mode = '1'
if input('是否使用默认Steam安装目录？(Y/N)') in{'Y', 'y'}:
    mode = '0'
    address_list = [r':\SteamLibrary\steamapps\common'+'\\',r':\Steam\steamapps\common'+'\\',r':\Program Files (x86)\Steam\steamapps\common'+'\\',r':\Program Files\Steam\steamapps\common'+'\\']
    for address in address_list:    
        for letter in alphabet_upper:
            if os.path.isdir(letter+address):
                file_lists=os.listdir(letter+address)
                dir_dict.update(dict(zip(file_lists,[letter+address+file_name+'\\' for file_name in file_lists if os.path.isdir(letter+address+file_name)])))
        if dir_dict=={}:
            print('未找到Steam安装目录，请手动输入')
            mode='1'
if mode=='1':
    address=input('请输入Steam安装目录：')
    address.replace('\\','\\\\')
    if os.path.isdir(address):
        file_lists=os.listdir(address)
        dir_dict.update(dict(zip(file_lists,[address+file_name+'\\' for file_name in file_lists if os.path.isdir(address+file_name)])))
        if dir_dict=={}:
            print('未找到Steam安装目录')
            os.system('pause')
            os._exit(1)
    else:
        print('输入错误，程序退出')
        os.system('pause')
        os._exit(1)
#爬取名字
weburl=r'https://store.steampowered.com/app/'
headers={'User-Agnet':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.41"}
cookies_str=r'timezoneOffset=28800,0'
try:
        cookies={}
        for line in cookies_str.split(';'):
            key, value = line.split('=', 1)
            cookies[key] = value
except ValueError:
    os._exit(1)
#计算相似度
def compare_name(dir_list,name_list):
    count=0
    max_count=0
    temp=dir_list[0]
    for name in dir_list:
        for word in name_list:
            if word in name:
                count+=1
        if count>max_count:
            max_count=count
            temp=name
        count=0
    return temp

            

# 获取文件夹中的所有文件名
def get_file_list(folder_path,type):
    file_list = os.listdir(folder_path)
    url_files = [file_name for file_name in file_list if file_name.endswith('.'+type)]
    #将文件名按照长度顺序排序
    url_files.sort(key=lambda x:len(x))
    return url_files
# 获取图标
def find_icon(id):
    url=weburl+id
    try:
        cat_response = get(url=url, headers=headers, cookies=cookies)
    except:
        print('连接Steam超时')
        os.system('pause')
        os._exit(1)
    pattern=r'<title>(Save.+on)?(.+)on Steam</title>'
    title=re.findall(pattern,cat_response.text)
    pattern=r'[A-Za-z0-9-_]+'
    name=re.findall(pattern,title[0][-1])
    name=compare_name(list(dir_dict.keys()),name)
    if name not in dir_dict:
        return
    if get_file_list(dir_dict[name],'ico')!=[]:
        icon=dir_dict[name]+get_file_list(dir_dict[name],'ico')[0]
    elif get_file_list(dir_dict[name],'exe')!=[]:
        icon=dir_dict[name]+get_file_list(dir_dict[name],'exe')[0]
    return icon
# 替换图标
def replace_icon(url_files,folder_path):
    # 打开文件并读取内容
    for file_name in url_files:
        with open(folder_path+"\\"+file_name, 'r') as file:
            content = file.read()
        # 获取图标路径
            pattern=r'URL=steam://rungameid/(.*)'
            id=re.findall(pattern,content)
            icon=find_icon(id[0])
            if icon==None:
                continue
            icon=icon.replace('\\','\\\\')
            content=re.sub(r'IconIndex=.*',r'IconIndex=0',content)
            content=re.sub(r'IconFile=.*',r'IconFile='+icon,content)
            print(file_name+' '+icon)
    # 替换文本
    #content = content.replace('old_text', 'new_text')
# 打开文件以写入模式，并将修改后的内容写入文件
            try:
                with open(folder_path+'\\'+file_name, 'w') as file:
                    file.write(content)
                file.close()
            except PermissionError:
                print(file_name+' Permission Denied')
                continue

def main():
    # 获取文件
    folder_path = os.getcwd()
    print('当前文件夹为：'+folder_path)
    url_files = get_file_list(folder_path,'url')
    # 替换图标
    print('替换图标中...')
    replace_icon(url_files,folder_path)
    print('当前文件夹已替换完成，尝试替换公共桌面快捷方式图标...')
    url_files = get_file_list(r'C:\Users\Public\Desktop','url')
    replace_icon(url_files,r'C:\Users\Public\Desktop')
    print('\n替换完成,过一段时间即可生效\n')
    print('如图标错误，请再次运行程序手动输入Steam安装目录\n如仍然错误,请手动修改快捷方式图标\n')
    print('如有其他问题，请联系作者\n')
    print(r'Github:https://github.com/Einck0/IconFix\n')
    os.system('pause')
if __name__ == "__main__":
    main()