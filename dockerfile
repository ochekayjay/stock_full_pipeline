FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt ${LAMBDA_TASK_ROOT}/

RUN pip install \
    --timeout 300 \
    --retries 10 \
    --no-cache-dir \
    -r ${LAMBDA_TASK_ROOT}/requirements.txt \
    --target ${LAMBDA_TASK_ROOT}

COPY main_function.py ${LAMBDA_TASK_ROOT}/

COPY config.yaml ${LAMBDA_TASK_ROOT}/

CMD ["extraction_and_loading_layer.handler"]