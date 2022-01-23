FROM public.ecr.aws/lambda/python:3.8

# Copy function code
COPY sync-from-stream.py ${LAMBDA_TASK_ROOT}

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .

RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

ENV TABLE_NAME=${DYNAMODB_TABLE_NAME}
ENV AWS_SECRET_NAME=${AWS_SECRET_NAME}

CMD [ "sync-from-stream.lambda_handler" ]