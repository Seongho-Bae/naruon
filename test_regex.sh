#!/bin/bash
strix_model="openai/gpt-4o"
case "$strix_model" in
  gpt-5.[4-9]* | gpt-5.[1-9][0-9]* | gpt-[6-9]* | gpt-[1-9][0-9]* | \
  openai/gpt-5.[4-9]* | openai/gpt-5.[1-9][0-9]* | openai/gpt-[6-9]* | openai/gpt-[1-9][0-9]*)
    echo 'enabled=true'
    ;;
  *)
    echo 'error'
    ;;
esac
