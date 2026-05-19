FROM public.ecr.aws/lambda/python:3.12

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy function code and tools
COPY lambda/orchestrator.py ${LAMBDA_TASK_ROOT}
COPY tools/ ${LAMBDA_TASK_ROOT}/tools/
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/

# Set the CMD to your handler
CMD ["orchestrator.lambda_handler"]
