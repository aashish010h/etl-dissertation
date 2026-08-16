FROM public.ecr.aws/lambda/python:3.12

# Install SSL root certificates
RUN microdnf update -y && microdnf install -y ca-certificates

# Copy requirements from the lambda folder and install
COPY lambda/requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy the ETL application from the src folder
COPY src/app.py ${LAMBDA_TASK_ROOT}

# Tell Lambda where the handler function is
CMD [ "app.lambda_handler" ]