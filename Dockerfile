# vim:set ft=dockerfile:
FROM felix/multicorn:9.6

ADD docker-entrypoint-initdb.d/ /docker-entrypoint-initdb.d/

ARG elasticsearch_pip_install_string
RUN pip install "$elasticsearch_pip_install_string"

RUN mkdir /esfdw

COPY setup.py /esfdw/
COPY esfdw/ /esfdw/

RUN python /esfdw/setup.py develop

VOLUME ["/esfdw"]
