FROM public.ecr.aws/lambda/python:3.12

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt --quiet

# Copy handler and metrics
COPY handler.py ${LAMBDA_TASK_ROOT}/
COPY metrics/ ${LAMBDA_TASK_ROOT}/metrics/

CMD ["handler.handler"]
