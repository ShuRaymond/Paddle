/* Copyright (c) 2016 PaddlePaddle Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. */

#include <string>
#include <vector>
#include "paddle/fluid/framework/op_registry.h"

namespace paddle {
namespace operators {

class SqueezeOpInferShape : public framework::InferShapeBase {
 public:
  void operator()(framework::InferShapeContext *ctx) const override {
    PADDLE_ENFORCE(ctx->HasInput("X"),
                   "Input(X) of SqueezeOp should not be null.");
    PADDLE_ENFORCE(ctx->HasOutput("Out"),
                   "Output(Out) of SqueezeOp should not be null.");

    const auto &x_dims = ctx->GetInputDim("X");
    // Check input tensor dims (<9).
    PADDLE_ENFORCE(x_dims.size() <= 9,
                   "Invalid dimnesions, dynamic dimensions must have "
                   "between [1, 9] dimensions.");

    const auto &axes = ctx->Attrs().Get<std::vector<int>>("axes");
    for (int a : axes) {
      PADDLE_ENFORCE_LT(a, x_dims.size(),
                        "The axis must be less than input tensor's rank.");
    }

    auto out_dims = GetOutputShape(axes, x_dims);
    ctx->SetOutputDim("Out", out_dims);
    // TODO(chenweihang): This share option is necessary?
    if (x_dims[0] == out_dims[0]) {
      // Only pass LoD when the first dimension of output and Input(X)
      // are the same.
      ctx->ShareLoD("X", "Out");
    }
  }

  static framework::DDim GetOutputShape(const std::vector<int> squeeze_dims,
                                        const framework::DDim &in_dims) {
    int num_squeeze_dims = squeeze_dims.size();
    int cnt_squeezed_dims = 0;
    bool should_squeeze[9] = {false};

    // Determines number of dimensions of output tensor after squeeze.
    // Mark and count the dimensions need to be squeezed
    if (num_squeeze_dims == 0) {
      for (int idx = 0; idx < in_dims.size(); ++idx) {
        if (in_dims[idx] == 1) {
          should_squeeze[idx] = true;
          ++cnt_squeezed_dims;
        }
      }
    } else {
      for (int idx = 0; idx < num_squeeze_dims; ++idx) {
        int current = squeeze_dims[idx] < 0 ? squeeze_dims[idx] + in_dims.size()
                                            : squeeze_dims[idx];
        // Check current index.
        PADDLE_ENFORCE(current >= 0,
                       "Invalid axis, negative axis is out of range.");
        // PADDLE_ENFORCE_LT(current, in_dims.size(), "Invalid axis is given.");
        PADDLE_ENFORCE(
            in_dims[current] == 1,
            "Invalid axis index, the axis will be squeezed should be 1.");

        if (!(should_squeeze[current])) {
          ++cnt_squeezed_dims;
        }
        should_squeeze[current] = true;
      }
    }

    // Make output dimensions
    std::vector<int64_t> output_shape(in_dims.size() - cnt_squeezed_dims, 0);
    for (int in_idx = 0, out_idx = 0; in_idx < in_dims.size(); ++in_idx) {
      if (!should_squeeze[in_idx]) {
        output_shape[out_idx++] = in_dims[in_idx];
      }
    }

    return framework::make_ddim(output_shape);
  }
};

class SqueezeOp : public framework::OperatorBase {
 public:
  SqueezeOp(const std::string &type, const framework::VariableNameMap &inputs,
            const framework::VariableNameMap &outputs,
            const framework::AttributeMap &attrs)
      : OperatorBase(type, inputs, outputs, attrs) {}

 private:
  void RunImpl(const framework::Scope &scope,
               const platform::Place &place) const override {
    auto &axes = Attr<std::vector<int>>("axes");
    auto x_dims = scope.FindVar(Input("X"))->Get<framework::LoDTensor>().dims();
    auto out_dims = SqueezeOpInferShape::GetOutputShape(axes, x_dims);

    framework::AttributeMap attrs;
    attrs["shape"] = framework::vectorize2int(out_dims);
    attrs["inplace"] = Attr<bool>("inplace");
    // Invoke Reshape Op
    auto reshape_op = framework::OpRegistry::CreateOp(
        "reshape", {{"X", {Input("X")}}, {"Shape", {}}},
        {{"Out", {Output("Out")}}}, attrs);
    reshape_op->Run(scope, place);
  }
};

class SqueezeOpMaker : public framework::OpProtoAndCheckerMaker {
 public:
  void Make() override {
    AddInput("X", "(Tensor). The input tensor of squeeze operator.");
    AddOutput("Out", "(Tensor). The output tensor of squeeze operator.");
    AddAttr<std::vector<int>>("axes",
                              "(std::vector<int>). List of positive integers,"
                              " indicate the dimensions to squeeze.")
        .SetDefault({});
    AddAttr<bool>("inplace",
                  "(default: false) Squeeze the source tensor's shape without "
                  "memory copy. When Attr(inplace) is set true, the output "
                  "tensor shares memory with Input(X), otherwise, a new output "
                  "tensor is created, and its data are copied from Input(x).")
        .SetDefault(false);
    AddComment(R"DOC(
        Squeeze Operator.
        
        Remove single-dimensional entries from the shape of a tensor. 
        Takes a parameter axes with a list of axes to squeeze. 
        If axes is not provided, all the single dimensions will be removed from the shape. 
        If an axis is selected with shape entry not equal to one, an error is raised.
        
        Examples:
        Case 1:
          Given 
            X.shape = (1, 3, 1, 5)
          and
            axes = [0]
          we get:
            Out.shape = (3, 1, 5)

        Case 2:
          Given
            X.shape = (1, 3, 1, 5)
          we get:
            Out.shape = (3, 5)
    )DOC");
  }
};

class SqueezeGradInferShape : public framework::InferShapeBase {
 public:
  void operator()(framework::InferShapeContext *context) const override {
    context->SetOutputDim(framework::GradVarName("X"),
                          context->GetInputDim("X"));
    context->ShareLoD("X", framework::GradVarName("X"));
  }
};

class SqueezeGradOp : public framework::OperatorBase {
 public:
  SqueezeGradOp(const std::string &type,
                const framework::VariableNameMap &inputs,
                const framework::VariableNameMap &outputs,
                const framework::AttributeMap &attrs)
      : OperatorBase(type, inputs, outputs, attrs) {}

 private:
  void RunImpl(const framework::Scope &scope,
               const platform::Place &place) const override {
    auto dx_name = Output(framework::GradVarName("X"));
    auto dout_name = Input(framework::GradVarName("Out"));
    auto x_dims = scope.FindVar(Input("X"))->Get<framework::LoDTensor>().dims();
    framework::AttributeMap attrs;
    attrs["shape"] = framework::vectorize2int(x_dims);
    attrs["inplace"] = Attr<bool>("inplace");

    auto reshape_op = framework::OpRegistry::CreateOp(
        "reshape", {{"X", {dout_name}}, {"Shape", {}}}, {{"Out", {dx_name}}},
        attrs);
    reshape_op->Run(scope, place);
  }
};

}  // namespace operators
}  // namespace paddle

// Tell linker to use reshape op
USE_OP(reshape);

namespace ops = paddle::operators;
REGISTER_OPERATOR(squeeze, ops::SqueezeOp, ops::SqueezeOpMaker,
                  ops::SqueezeOpInferShape,
                  paddle::framework::DefaultGradOpDescMaker<true>);
REGISTER_OPERATOR(squeeze_grad, ops::SqueezeGradOp, ops::SqueezeGradInferShape);
