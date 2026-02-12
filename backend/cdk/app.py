#!/usr/bin/env python3
"""CDK app entry point for Trump304 backend infrastructure."""

import aws_cdk as cdk
from stacks.trump304_stack import Trump304Stack

app = cdk.App()
Trump304Stack(
    app, "Trump304Stack",
    env=cdk.Environment(region="ap-south-1"),
)
app.synth()
