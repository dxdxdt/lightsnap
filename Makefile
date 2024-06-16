all: lambda_function.zip lambda_layer.zip

lambda_function.zip: src
	cd src && zip -x '*/__pycache__/*' -x '__pycache__/*' -r ../lambda_function.zip *

lambda_layer.zip:
	python3.12 -m venv python
	source python/bin/activate && \
		python3.12 -m pip install \
			--target python/lib/python3.12/site-packages \
			--platform manylinux2014_aarch64 \
			--only-binary=:all: \
			"pyjson5" "boto3"
	zip -i 'python/lib/*' -r lambda_layer.zip python

clean:
	rm -rf lambda_function.zip lambda_function lambda_layer.zip python
