FROM alpine
CMD sh -c "echo PORT is ${PORT:-3000}"
