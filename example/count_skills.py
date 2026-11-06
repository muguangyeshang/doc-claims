#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""示例真值源：数一遍 example/data 里的"技能"。真值必须来自当场重算，不来自文档。"""
import os
import sys

data = os.path.join(os.path.dirname(__file__), "data")
n = sum(1 for f in os.listdir(data) if f.endswith(".skill.md"))
print(n)
sys.exit(0)
