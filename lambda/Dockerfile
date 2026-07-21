# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.12

# Copy the Lambda requirements and install them
COPY lambda/requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

# Copy the unified ETL script into the Lambda task root
COPY src/app.py ${LAMBDA_TASK_ROOT}

# Tell Lambda where the execution handler is located
CMD ["app.lambda_handler"]