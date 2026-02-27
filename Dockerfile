# Use AWS Lambda base image for Python
FROM public.ecr.aws/lambda/python:3.10

# Install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy entire project to Lambda's task root
COPY . ${LAMBDA_TASK_ROOT}/

# Create artifacts directory
RUN mkdir -p ${LAMBDA_TASK_ROOT}/artifacts

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Tell Lambda to run our handler
CMD ["lambda_handler.handler"]