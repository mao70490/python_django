from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage
from invoiceapi.models import users
from module import func

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            if isinstance(event, MessageEvent):
                userid = event.source.user_id
                if not users.objects.filter(uid=userid).exists():
                    unit = users.objects.create(uid=userid, state='no')
                    unit.save()
                mtext = event.message.text
                if mtext == '@使用說明':
                    func.sendUse(event)

                elif mtext == '@顯示本期中獎號碼':
                    func.showCurrent(event)

                elif mtext == '@顯示前期中獎號碼':
                    func.showOld(event)

                elif mtext == '@輸入發票最後三碼':
                    line_bot_api.reply_message(event.reply_token,TextSendMessage(text='請輸入發票最後三碼進行對獎！'))

                elif len(mtext) == 3 and mtext.isdigit():
                    func.show3digit(event, mtext, userid)

                elif len(mtext) == 5 and mtext.isdigit():
                    func.show5digit(event, mtext, userid)

        return HttpResponse()

    else:
        return HttpResponseBadRequest()
