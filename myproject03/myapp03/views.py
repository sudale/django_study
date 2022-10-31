import csv
from myapp03.models import Forecast
from .forms import UserForm
from django.contrib.auth import authenticate, login

from django.views.decorators.csrf import csrf_exempt
from myapp03.models import Board, Comments
import urllib.parse
import math
from django.db.models import Q
from django.shortcuts import HttpResponse, render, redirect, get_object_or_404
from django.http.response import JsonResponse

from myapp03 import bigdataProcess
from django.db.models.aggregates import Count
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import json


import requests
from bs4 import BeautifulSoup

# Create your views here.
UPLOAD_DIR = 'C:\\djangostudy\\upload\\'


def melon(request):
    datas = []
    bigdataProcess.melon_crawing(datas)
    return render(request, 'bigdata/melon.html', {'datas': datas})


def weather(request):
    last_date = Forecast.objects.values('tmef').order_by('-tmef')[:1]
    print('last_date :', len(last_date))
    weather = {}
    bigdataProcess.weather_crawing(last_date, weather)

    print('last_date query :', str(last_date.query))

    # for i in weather:
    #     for j in weather[i]:
    #         dto = Forecast(city=i, tmef=j[0], wf=j[1], tmn=j[2], tmx=j[3])
    #         dto.save()

    weather_data = Forecast.objects.all()
    result = Forecast.objects.filter(city='부산')
    result1 = Forecast.objects.filter(city='부산').values(
        'wf').annotate(dcount=Count('wf')).values("dcount", "wf")
    print('result1 query :', str(result1.query))

    df = pd.DataFrame(result1)

    image_dic = bigdataProcess.weather_make_chart(result1, df.wf, df.dcount)
    return render(request, 'bigdata/weather_chart.html', {"img_data": image_dic, "weather_data": weather_data})


def map(request):
    bigdataProcess.map()
    return render(request, "bigdata/map.html")


def wordcloud(request):
    w_path = 'C:\\djangostudy\\myProject03\\data\\'
    data = json.loads(open(w_path+'4차 산업혁명.json',
                      'r', encoding='utf-8').read())
    # print(data)
    bigdataProcess.make_wordCloud(data)
    return render(request, "bigdata/wordchart.html", {"img_data": "k_wordCloud.png"})


def attendance(request):

    req = requests.get(
        'https://www.koreabaseball.com/History/Crowd/GraphDaily.aspx')
    soup = BeautifulSoup(req.text, 'html.parser')
    # print(soup)

    bigdataProcess.attendance(soup)
    return render(request, "bigdata/attendance.html", {"img_data": "KBO_attendance.png"})

################# 게시판 ########################


def index(request):
    return render(request, 'base.html')


@ login_required(login_url='/login/')
def write_form(request):
    return render(request, 'board/insert.html')


@ csrf_exempt
def insert(request):
    fname = ''
    fsize = 0
    if 'file' in request.FILES:
        file = request.FILES['file']
        fname = file.name
        fsize = file.size
        fp = open('%s%s' % (UPLOAD_DIR, fname), 'wb')
        for chunk in file.chunks():
            fp.write(chunk)
        fp.close()

    dto = Board(writer=request.user,
                title=request.POST['title'],
                content=request.POST['content'],
                filename=fname,
                filesize=fsize
                )
    dto.save()
    return redirect('/base')


def list(request):
    page = request.GET.get('page', '1')
    word = request.GET.get('word', '')
    field = request.GET.get('field', 'title')

    if field == 'all':
        boardCount = Board.objects.filter(Q(writer__contains=word) | Q(
            title__contains=word) | Q(content__contains=word)).count()
    elif field == 'writer':
        boardCount = Board.objects.filter(Q(writer__contains=word)).count()
    elif field == 'title':
        boardCount = Board.objects.filter(Q(title__contains=word)).count()
    elif field == 'content':
        boardCount = Board.objects.filter(Q(content__contains=word)).count()
    else:
        boardCount = Board.objects.all().count()

    pageSize = 5  # 한 화면에 게시글 수
    blockPage = 3  # 보이는 페이지 수
    currentPage = int(page)
    # 게시글 수 32 : pagesize:5
    start = (currentPage-1)*pageSize
    totPage = math.ceil(boardCount/pageSize)  # 게시글의 전체 페이지 수
    startPage = math.floor((currentPage - 1)/blockPage)*blockPage + 1
    endPage = startPage + blockPage - 1

    rowNo = boardCount-(int(page)-1)*pageSize
    if endPage > totPage:
        endPage = totPage  # endPage = 7

    if field == 'all':
        boardList = Board.objects.filter(Q(writer__contains=word) | Q(title__contains=word) | Q(
            content__contains=word)).order_by('-idx')[start:start+pageSize]
    elif field == 'writer':
        boardList = Board.objects.filter(
            Q(writer__contains=word)).order_by('-idx')[start:start+pageSize]
    elif field == 'title':
        boardList = Board.objects.filter(
            Q(title__contains=word)).order_by('-idx')[start:start+pageSize]
    elif field == 'content':
        boardList = Board.objects.filter(
            Q(content__contains=word)).order_by('-idx')[start:start+pageSize]
    else:
        boardList = Board.objects.all().order_by('-idx')[start:start+pageSize]

    context = {'boardList': boardList,
               'startPage': startPage,
               'blockPage': blockPage,
               'endPage': endPage,
               'totPage': totPage,
               'boardCount': boardCount,
               'currentPage': currentPage,
               'field': field,
               'word': word,
               'rowNo': rowNo,
               'range': range(startPage, endPage+1)}
    return render(request, 'board/list.html', context)


def download_count(request):
    id = request.GET['idx']
    dto = Board.objects.get(idx=id)
    dto.down_up()
    dto.save()
    count = dto.down
    return JsonResponse({'idx': id, 'count': count})


# 다운로드
def download(request):
    id = request.GET['idx']
    dto = Board.objects.get(idx=id)
    path = UPLOAD_DIR+dto.filename
    filename = urllib.parse.quote(dto.filename)

    with open(path, 'rb') as file:
        response = HttpResponse(file.read(),
                                content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment;filename*=UTF-8''{0}'.format(
            filename)
    return response


def detail(request, board_idx):
    dto = Board.objects.get(idx=board_idx)
    dto.hit_up()
    dto.save()

    # commentList= Comments.objects.filter(board_idx=board_idx).order_by('-idx')

    return render(request, 'board/detail.html', {'dto': dto})


def update(request, board_idx):
    dto = Board.objects.get(idx=board_idx)
    return render(request, 'board/update.html', {'dto': dto})


# 수정
@csrf_exempt
def update_now(request):
    id = request.POST['idx']
    dto = Board.objects.get(idx=id)
    fname = dto.filename
    fsize = dto.filesize

    if 'file' in request.FILES:
        file = request.FILES['file']
        fname = file.name
        fsize = file.size
        fp = open('%s%s' % (UPLOAD_DIR, fname), 'wb')
        for chunk in file.chunks():
            fp.write(chunk)
        fp.close()

    update_dto = Board(
        id,
        writer=request.user,
        title=request.POST['title'],
        content=request.POST['content'],
        filename=fname,
        filesize=fsize
    )
    update_dto.save()
    return redirect('/list')


def delete(request, board_idx):
    dto = Board.objects.get(idx=board_idx)
    dto.delete()
    return redirect('/list')


def delete(request, writer_idx):
    dto = Comments.objects.get(idx=writer_idx)
    dto.delete()
    return redirect('/list')


@csrf_exempt
@login_required(login_url='/login/')
def comment_insert(request):
    id = request.POST['idx']
    board = get_object_or_404(Board, pk=id)
    dto = Comments(
        board=board,
        writer=request.user,
        content=request.POST['Comment']
    )
    dto.save()
    return redirect('/detail/'+id)


def signup(request):
    if request.method == "POST":  # 회원가입 insert
        form = UserForm(request.POST)
        if form.is_valid():
            print('signup POST valid')
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)

            login(request, user)
            return redirect('/')
        else:
            print('signup POST un_valid')

    else:  # 회원가입 폼으로
        form = UserForm()

    return render(request, 'common/signup.html', {'form': form})
