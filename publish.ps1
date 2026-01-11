# Copyright (c) 2026 github.com/fastshell
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

rm -Recursive -Force -Path ./dist/
poetry build
poetry publish