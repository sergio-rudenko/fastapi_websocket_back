import os
import sys
import uvicorn

if __name__ == '__main__':
    try:
        print(sys._MEIPASS)
        print(os.listdir(sys._MEIPASS))
    except Exception as e:
        print('Exception:', e)
        pass

    ''' START '''
    uvicorn.run('app:app', host='0.0.0.0', port=8888, reload=False)
    print('exiting...')
