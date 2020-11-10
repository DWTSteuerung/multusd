#!/usr/bin/env bash
#
# 2020-08-08
# do all .proto files 

cd /multus/lib/proto
python3 -m grpc_tools.protoc --proto_path=. ./LANWANOVPNCheck.proto --python_out=. --grpc_python_out=.
python3 -m grpc_tools.protoc --proto_path=. ./multusOVPNClient.proto --python_out=. --grpc_python_out=.
python3 -m grpc_tools.protoc --proto_path=. ./multusReadDIDO.proto --python_out=. --grpc_python_out=.
