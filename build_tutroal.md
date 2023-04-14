# 构建教程
本教程是在 windows系统下构建本工具包的教程

推荐使用anaconda进行python环境的配置

需要下载安装  [Microsoft Visual C++ Compiler Package for Python 2.7](https://web.archive.org/web/20200709160228if_/https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi) 以备python 2.7 安装依赖时的构建

需要修改构建的参数
anaconda3\envs\py2\Lib\distutils\msvc9compiler.py
结合实际情况修改242到257

![image.png](https://s2.loli.net/2023/04/12/hlcioMkgvmExrNX.png)

## conda 环境配置

### 导入环境
```
conda env create -f environment.yaml
```
### 激活环境

```bash
conda activate py2
```

## 手动安装相关包

从3rd 文件夹中手动安装 comtypes

```
pip install 3rd/comtypes-1.1.6-py2-none-any.whl
```

### 手动安装 py2exe

如果是32位的可以用`whl`安装

* 方法一 下载源码构建

    [[source] py2exe-0.6.9](https://udomain.dl.sourceforge.net/project/py2exe/py2exe/0.6.9/py2exe-0.6.9.zip)

    从源码构建的话需要修改

    https://blog.csdn.net/secretx/article/details/17472107

* 方法二 直接安装conda包

    从3rd文件夹本地安装
    ```bash
    conda install --use-local 3rd/py2exe-0.6.9-py27-win64.tar.bz2
    ```

测试软件 

手动构建exe

设置环境变量

修复tee错误
$Env:Path+=';C:\Program Files\Git\usr\bin
修复找不到vcarsd
$Env:VS90COMNTOOLS=$Env:LOCALAPPDATA+'\Programs\Common\Microsoft\Visual C++ for Python\9.0\'