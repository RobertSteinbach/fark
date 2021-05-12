FROM python:3
ADD fark.py /
RUN pip install beautifulsoup4
RUN pip install requests
CMD [ "python3","./fark.py" ]
