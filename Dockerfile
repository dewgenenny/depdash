FROM python:3


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY update_stats.py /
# Install the function's dependencies using file requirements.txt
# from your project folder.

#HEALTHCHECK --interval=30s --timeout=5s --retries=2 \
#  CMD ["/probe.sh"]


#COPY requirements.txt  .
#RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "python3", "/update_stats.py" ]


#CMD ["/bin/entrypoint.sh"]



