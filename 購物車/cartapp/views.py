from django.shortcuts import render,redirect
from cartapp import models
from smtplib import SMTP,SMTPAuthenticationError,SMTPException
from email.mime.text import MIMEText

message=''
cartlist=[]
customname=''
customphone=''
customadr=''
customemail=''

def index(request):
    global cartlist
    if 'cartlist' in request.session: #若session中存在cartlist就讀出
        cartlist=request.session['cartlist']
    else:  #重新購物
        cartlist=[]
    cartnum=len(cartlist)  #購買商品筆數
    productall=models.ProductModel.objects.all()  #取得資料庫所有商品
    return render(request,'index.html',locals())

def detail(request,productid=None):
    product=models.ProductModel.objects.get(id=productid)
    return render(request,'detail.html',locals())

def cart(request):
    global cartlist
    cartlist1=cartlist
    tot=0
    for unit in cartlist:
        tot+=int(unit[3])
    if tot==0:
        grandtotal=tot
    else:
        grandtotal=tot+100
    return render(request,'cart.html',locals())

def addtocart(request,ctype=None,productid=None):
    global cartlist
    if ctype=='add': #加入購物車
        product=models.ProductModel.objects.get(id=productid)
        flag=True #設檢查旗標為True
        for unit in cartlist:  #逐筆檢查商品是否已存在
            if product.pname==unit[0]:  #商品已存在
                unit[2]=str(int(unit[2])+1)  #數量加1
                unit[3]=str(int(unit[3])+product.pprice)  #計算價錢
                flag=False  #設檢查旗標為False
                break
        if flag:  #商品不存在
            temlist=[]  #暫時串列
            temlist.append(product.pname)  #將商品資料加入暫時串列
            temlist.append(str(product.pprice))  #商品價格
            temlist.append('1')  #先暫訂數量為1
            temlist.append(str(product.pprice))  #總價
            cartlist.append(temlist)  #將暫時串列加入購物車
        request.session['cartlist']=cartlist  #購物車寫入session
        return redirect('/cart/')
    elif ctype=='update':  #更新購物車
        n=0
        for unit in cartlist:
            unit[2]=request.POST.get('qty'+str(n),'1') #取得數量
            unit[3]=str(int(unit[1])*int(unit[2])) #取得總價
            n+=1
        request.session['cartlist']=cartlist
        return redirect('/cart/')
    elif ctype=='empty':  #清空購物車
        cartlist=[]  #設購物車為空串列
        request.session['cartlist']=cartlist
        return redirect('/index/')
    elif ctype=='remove':  #刪除購物車中商品
        del cartlist[int(productid)]  #從購物車串列中移除商品
        request.session['cartlist']=cartlist
        return redirect('/cart/')

def cartorder(request): #按我要結帳鈕
    global cartlist,message,customadr,customname,customphone,customemail
    cartlist1=cartlist
    tot=0
    for unit in cartlist: #計算商品總金額
        tot+=int(unit[3])
    if tot>0:
        grandtotal=tot+100        
    else:
        return redirect('/cart/')
    customname1=customname  #以區域變數傳給模版
    customphone1=customphone
    customadr1=customadr
    customemail1=customemail
    message1=message
    return render(request,'cartorder.html',locals())

def cartok(request): #按確認購買鈕
    global cartlist,message,customadr,customname,customphone,customemail
    tot=0
    for unit in cartlist:
        tot+=int(unit[3])
    grandtotal=tot+100
    message=''
    customname=request.POST.get('CustomerName','')
    customphone=request.POST.get('CustomerPhone','')
    customadr=request.POST.get('CustomerAdr','')
    customemail=request.POST.get('CustomerEmail','')
    paytype=request.POST.get('paytype','')
    customname1=customname
    if customname=='' or customphone=='' or customadr=='' or customemail=='':
        message='姓名、電話、住址、電子郵件皆需輸入'
        return redirect('/cartorder/')
    else:
        unitorder=models.OrderModel.objects.create(subtotal=tot,shipping=100,grandtotal=grandtotal, customname=customname, customphone=customphone, customadr=customadr, customemail=customemail, paytype=paytype) #建立訂單
        for unit in cartlist: #將購買商品寫入資料庫
            tot=int(unit[1])*int(unit[2])
            unitdetail=models.DetailModel.objects.create(dorder=unitorder,pname=unit[0],unitprice=unit[1],quantity=unit[2],dtotal=tot)
        orderid=unitorder.id
        mailfrom="你的gmail帳號"  #帳號
        mailpw="你的gmail密碼"  #密碼
        mailto=customemail  #客戶的電子郵件
        mailsubject="訂單通知";  #郵件標題
        mailcontent="感謝您的光臨，您已經成功的完成訂購程序。\n我們將儘快把您選購的商品郵寄給您！ 再次感謝您支持\n您的訂單編號為：" + str(orderid) + "，您可以使用這個編號回到網站中查詢訂單的詳細內容。" #郵件內容
        send_simple_message(mailfrom,mailpw,mailto,mailsubject,mailcontent)
        cartlist=[]
        request.session['cartlist']=cartlist
        return render(request,'cartok.html',locals())

def cartordercheck(request):  #查詢訂單
    orderid=request.GET.get('orderid','')  #取得輸入id
    customemail=request.GET.get('customemail','')  #取得輸email
    if orderid=='' and customemail=='':  #按查詢訂單鈕
        firstsearch=1
    else:
        order=models.OrderModel.objects.filter(id=orderid).first()
        if order==None or order.customemail !=customemail:  #查不到資料
            notfound=1
        else:  #找到符合的資料
            details=models.DetailModel.objects.filter(dorder=order)
    return render(request,'cartordercheck.html',locals())

def send_simple_message(mailfrom,mailpw,mailto,mailsubject,mailcontent): #寄信
    global message
    strSmtp='smtp.gmail.com:587' #主機
    strAccount = mailfrom  #帳號
    strPassword = mailpw  #密碼
    msg=MIMEText(mailcontent)
    msg['Subject']=mailsubject  #郵件標題
    mailto1=mailto  #收件者
    server=SMTP(strSmtp)  #建立SMTP連線
    server.ehlo()  #跟主機溝通
    server.starttls()  #TTLS安全認證
    try:
        server.login(strAccount,strPassword)  #登入
        server.sendmail(strAccount,mailto1,msg.as_string())  #寄信
    except SMTPAuthenticationError:
        message="無法登入！"
    except:
        message="郵件發送產生錯誤！"
    server.quit()  #關閉連線