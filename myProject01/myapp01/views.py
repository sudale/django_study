from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render

from myapp01.models import Board

# Create your views here.
UPLOAD_DIR = 'C:\\djangostudy\\upload'

# write_form


def write_form(request):
    return render(request, 'board/write.html')


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


# 전체보기
def list(request):
    boardList = Board.objects.all()
    context = {'boardList': boardList}
    return render(request, 'board/list.html', context)


# 상세보기
def detail_idx(request):
    id = request.GET['idx']
    dto = Board.objects.get(idx=id)
    dto.hit_up()
    dto.save()
    return render(request, 'board/detail.html', {'dto': dto})


# 상세보기(detail/5)
def detail(request, board_idx):
    # print('board_idx :', board_idx)

    dto = Board.objects.get(idx=board_idx)
    dto.hit_up()
    dto.save()
    return render(request, 'board/detail.html', {'dto': dto})


# 수정하기 폼
def update_form(request, board_idx):
    dto = Board.objects.get(idx=board_idx)
    dto.save()
    return render(request, 'board/update.html', {'dto': dto})


# 수정
@csrf_exempt
def update(request):

    # 파일 그대로
    id = request.POST['idx']
    dto = Board.objects.get(idx=id)
    fname = dto.filename
    fsize = dto.filesize

    # 파일 업데이트시
    if 'file' in request.FILES:
        file = request.FILES['file']
        fname = file.name
        fsize = file.size
        fp = open('%s%s' % (UPLOAD_DIR, fname), 'wb')
        for chunk in file.chunks():
            fp.write(chunk)
        fp.close()

    update_dto = Board(  # idx=request.POST['idx'],
        id,
        writer=request.POST['writer'],
        title=request.POST['title'],
        content=request.POST['content'],
        filename=fname,
        filesize=fsize
    )

    update_dto.save()
    return redirect('/list')


# 삭제
def delete(request, board_idx):
    dto = Board.objects.get(idx=board_idx)
    dto.delete()
    return redirect('/list')
