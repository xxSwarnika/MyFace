FROM python:3.13-trixie

ARG TIMEZONE
ARG USE_GIT 
ARG UID
ARG GID
ARG PORT
ARG LOG_DIR
ARG MYFACE_PATH
ARG MYFACE_SRC
ARG START_DIR
ENV APP_NAME=myface
ENV PORT=${PORT:-8000}
#ENV LOG_DIR=${LOG_DIR:-/var/log/${APP_NAME}}
ENV UID=${UID:-222}
ENV GID=${GID:-222}
ENV INSTALL_DIR=/srv/$APP_NAME
ENV START_DIR=${START_DIR:-${INSTALL_DIR}}
ENV HOME=/home/$APP_NAME

RUN apt-get -y update && apt-get -y install tzdata less vim bubblewrap && apt-get clean && rm -rf /var/lib/apt/lists/* 
RUN if [ ! -z "$TIMEZONE" ]; then rm -f /etc/localtime && ln -s "/usr/share/zoneinfo/$TIMEZONE" /etc/localtime && echo "$TIMEZONE" > /etc/timezone; fi

# create a user if needed
RUN if [ ! -z "$GID" ] && ! id -g $GID 2>/dev/null; then addgroup --system --gid $GID ${APP_NAME}; fi; if ! id $APP_NAME 2>/dev/null; then adduser --system ${UID:+--uid $UID} ${GID:+--gid $GID} --home "$HOME" $APP_NAME ; fi

# where we put the venv
ENV VENV=$HOME/venv


# Create log dir, if any, and make it writable by us
RUN if [ ! -z "$LOG_DIR" -a ! -d "$LOG_DIR" ]; then mkdir -p "$LOG_DIR" ; chown $APP_NAME "$LOG_DIR" ; fi

# If we're not using a port, make a directory for a Unix socket
RUN if [ -z $PORT ]; then mkdir -p /run/$APP_NAME; chown $APP_NAME /run/$APP_NAME; fi

USER $APP_NAME
WORKDIR $INSTALL_DIR

# Create venv and install dependencies
RUN --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt \
    python -m venv "$VENV" && . "$VENV/bin/activate" && pip install --only-binary :all: gunicorn hatch hatchling && cd /tmp && pip install --only-binary :all: -r /tmp/requirements.txt
COPY myface ${INSTALL_DIR}/myface
RUN --mount=type=bind,source=.,target=/tmp/src \
    mkdir -p ${INSTALL_DIR}/instance && cp /tmp/src/instance/*.cfg ${INSTALL_DIR}/instance/

# For manual debugging
COPY <<EOF $HOME/.bashrc
. $VENV/bin/activate
EOF
# force startup file for dash:
ENV ENV=$HOME/.bashrc

# Startup script
COPY --chmod=755 <<EOF $HOME/run-it.sh
    . $VENV/bin/activate
    if [ ! -z "$LOG_DIR" ]; then
        LOGGING="--access-logfile $LOG_DIR/access.log --error-logfile $LOG_DIR/error.log"
        export MYFACE_LOG_DIR=${LOG_DIR}
    else
        LOGGING="--access-logfile - --error-logfile -"
    fi
    # LOGGING="\$LOGGING --log-level debug"
    if [ -z "$PORT" ]; then
        BIND="--bind unix:/run/$APP_NAME/gunicorn.sock"
    else
        BIND="--bind 0.0.0.0:$PORT"
    fi
    LOG_FORMAT='%({x-real-ip}i)s %(l)s %({x-user}o)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
    cd "${START_DIR}" 
    export MYFACE_BASE_DIR=${INSTALL_DIR}
    export MYFACE_APP_NAME=${APP_NAME}
    export SCRIPT_NAME=
    export MYFACE_TRUST_X_REAL_IP=True
    RELOADS='--reload'
    for f in ${APP_NAME}/templates/*.html; do
        if [ -f "\$f" ]; then
            RELOADS="\$RELOADS --reload-extra-file \$f"
        fi
    done
    exec gunicorn \$BIND \$LOGGING --access-logformat="\$LOG_FORMAT" \$RELOADS  "${APP_NAME}:create_app()"
EOF


RUN cat $HOME/run-it.sh ;  id
EXPOSE $PORT
CMD ["/bin/sh", "-c", "$HOME/run-it.sh"]
