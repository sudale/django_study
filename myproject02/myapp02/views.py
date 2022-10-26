import math
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator

from django.db.models import Q
import urllib.parse

from sympy import content

from myapp02.models import Board, Comment

# Create your views here.
UPLOAD_DIR = 'C:\\djangostudy\\upload\\'


def index(request):
    return render(request, 'base.html')


def write_form(request):
    return render(request, 'board/insert.html')


# insert
@csrf_exempt
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

    dto = Board(writer=request.POST['writer'],
                title=request.POST['title'],
                content=request.POST['content'],
                filename=fname,
                filesize=fsize
                )
    dto.save()
    return redirect('/list/')


def list(request):
    page = request.GET.get('page', 1)
    word = request.GET.get('word', '')
    field = request.GET.get('field', 'title')

    # count
    if field == 'all':
        boardCount = Board.objects.filter(Q(writer__contains=word) |
                                          Q(title__contains=word) |
                                          Q(content__contains=word)).count()
        # __ like와 같은말
    elif field == 'writer':
        boardCount = Board.objects.filter(
            Q(writer__contains=word)).count()

    elif field == 'title':
        boardCount = Board.objects.filter(
            Q(title__contains=word)).count()

    elif field == 'content':
        boardCount = Board.objects.filter(
            Q(content__contains=word)).count()

    else:
        boardCount = Board.objects.all().count()

    pageSize = 5  # 한 화면 게시글 수
    blockPage = 3  # 보이는 페이지 수
    currentPage = int(page)

    start = (currentPage-1)*pageSize
    totPage = math.ceil(boardCount / pageSize)  # 게시글의 전체 페이지수
    startPage = math.floor((currentPage-1)/blockPage)*blockPage + 1
    endPage = startPage + blockPage - 1

    if endPage > totPage:
        endPage = totPage

    if field == 'all':
        boardList = Board.objects.filter(Q(writer__contains=word) |
                                         Q(title__contains=word) |
                                         Q(content__contains=word)).order_by('-id')[start:start+pageSize]
        # __ like와 같은말
    elif field == 'writer':
        boardList = Board.objects.filter(
            Q(writer__contains=word)).order_by('-id')[start:start+pageSize]

    elif field == 'title':
        boardList = Board.objects.filter(
            Q(title__contains=word)).order_by('-id')[start:start+pageSize]

    elif field == 'content':
        boardList = Board.objects.filter(
            Q(content__contains=word)).order_by('-id')[start:start+pageSize]

    else:
        boardList = Board.objects.all().order_by('-id')[start:start+pageSize]

    context = {'boardList': boardList,
               'startPage': startPage,
               'blockPage': blockPage,
               'endPage': endPage,
               'totPage': totPage,
               'boardCount': boardCount,
               'currentPage': currentPage,
               'field': field,
               'word': word,
               'range': range(startPage, endPage+1)
               }
    return render(request, 'board/list.html', context)


def download_count(request):
    id = request.GET['id']

    dto = Board.objects.get(id=id)
    dto.down_up()
    dto.save()
    count = dto.down

    return JsonResponse({'id': id, 'count': count})


def download(request):
    id = request.GET['id']
    dto = Board.objects.get(id=id)
    path = UPLOAD_DIR+dto.filename

    filename = urllib.parse.quote(dto.filename)
    print('filename :', filename)
    with open(path, 'rb') as file:
        response = HttpResponse(
            file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = "attachment;filename*=UTF-8''{0}".format(
            filename)
    return response


def list_page(request):
    page = request.GET.get('page', '1')
    word = request.GET.get('word', '')

    boardCount = Board.objects.filter(Q(writer__contains=word) |
                                      Q(title__contains=word) |
                                      Q(content__contains=word)).count()
    boardList = Board.objects.filter(Q(writer__contains=word) |
                                     Q(title__contains=word) |
                                     Q(content__contains=word)).order_by('-id')

    pageSize = 5

    # 페이징처리
    paginator = Paginator(boardList, pageSize)  # import 필요
    page_obj = paginator.get_page(page)
    print('boardCount :', boardCount)

    context = {'page_list': page_obj,
               'page': page,
               'word': word,
               'boardCount': boardCount}
    return render(request, 'board/list_page.html', context)


def detail_id(request):
    id = request.GET['id']
    dto = Board.objects.get(id=id)
    dto.hit_up()
    dto.save()

    # commentList
    # commentList = Comment.objects.filter(board_id=id).order_by('-id')
    return render(request, 'board/detail.html',
                  {'dto': dto})


def detail(request, board_id):
    dto = Board.objects.get(id=board_id)
    dto.hit_up()
    dto.save()

    # commentList = Comment.objects.filter(board_id=board_id).order_by('-id')
    return render(request, 'board/detail.html', {'dto': dto})
