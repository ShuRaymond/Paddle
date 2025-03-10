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

#include <memory>
#include <string>
#include <unordered_map>

#include "paddle/fluid/framework/infershape_utils.h"
#include "paddle/fluid/framework/op_registry.h"
#include "paddle/fluid/platform/device/gpu/gpu_dnn.h"
#include "paddle/phi/core/infermeta_utils.h"
#include "paddle/phi/infermeta/backward.h"
#include "paddle/phi/infermeta/unary.h"

namespace paddle {
namespace operators {

class SoftmaxOp : public framework::OperatorWithKernel {
 public:
  using framework::OperatorWithKernel::OperatorWithKernel;

 protected:
  framework::OpKernelType GetExpectedKernelType(
      const framework::ExecutionContext& ctx) const override {
    // choose cudnn kernel if the runtime supported.
    std::string data_format = ctx.Attr<std::string>("data_format");
    phi::DataLayout layout_ = phi::StringToDataLayout(data_format);
    auto input_data_type = OperatorWithKernel::IndicateVarDataType(ctx, "X");
    if (input_data_type == framework::proto::VarType::FP16) {
      PADDLE_ENFORCE_EQ(
          platform::is_gpu_place(ctx.GetPlace()) ||
              platform::is_npu_place(ctx.GetPlace()) ||
              platform::is_xpu_place(ctx.GetPlace()) ||
              platform::is_mlu_place(ctx.GetPlace()) ||
              platform::is_custom_place(ctx.GetPlace()),
          true,
          platform::errors::InvalidArgument(
              "float16 can only be used on GPU/NPU/XPU/MLU and custom place"));
    }
    return framework::OpKernelType(input_data_type, ctx.GetPlace(), layout_);
  }
};

class SoftmaxOpMaker : public framework::OpProtoAndCheckerMaker {
 public:
  void Make() override {
    AddInput("X",
             "The input tensor of softmax, "
             "whose dimension :attr:`axis` is the input_feature_dimensions.");
    AddOutput("Out", "The normalized values with the same shape as X.");
    AddAttr<int>("axis",
                 "The dimension index of Input(x) to perform softmax,"
                 "default -1 for last dimension")
        .SetDefault(-1);
    AddAttr<std::string>(
        "data_format",
        "(string, default NCHW) Only used in "
        "An optional string from: \"NHWC\", \"NCHW\". "
        "Defaults to \"NHWC\". Specify the data format of the output data, "
        "the input will be transformed automatically. ")
        .SetDefault("AnyLayout");
    AddAttr<bool>(
        "use_cudnn",
        "(bool, default false) Only used in cudnn kernel, need install cudnn")
        .SetDefault(false)
        .AsExtra();
    AddComment(R"DOC(
Softmax Operator.

The input of the softmax operator is a tensor of any rank. The output tensor
has the same shape as the input.

The dimension :attr:`axis` of the input tensor will be permuted to the last.
Then the input tensor will be logically flattened to a 2-D matrix. The matrix's
second dimension(row length) is as same as the dimension :attr:`axis` of the input
tensor, and the first dimension(column length) is the product of all other
dimensions of the input tensor. For each row of the matrix, the softmax operator
squashes the K-dimensional(K is the width of the matrix, which is also the size
of the input tensor's dimension :attr:`axis`) vector of arbitrary real values to a
K-dimensional vector of real values in the range [0, 1] that add up to 1.
It computes the exponential of the given dimension and the sum of exponential
values of all the other dimensions in the K-dimensional vector input.
Then the ratio of the exponential of the given dimension and the sum of
exponential values of all the other dimensions is the output of the softmax
operator.

For each row $i$ and each column $j$ in the matrix, we have:
    $$Out[i, j] = \frac{\exp(X[i, j])}{\sum_j(exp(X[i, j])}$$

)DOC");
  }
};

class SoftmaxOpInferVarType : public framework::PassInDtypeAndVarTypeToOutput {
 protected:
  std::unordered_map<std::string, std::string>& GetInputOutputWithSameType()
      const override {
    static std::unordered_map<std::string, std::string> m{{"X", /*->*/ "Out"}};
    return m;
  }
};

class SoftmaxOpGrad : public framework::OperatorWithKernel {
 public:
  using framework::OperatorWithKernel::OperatorWithKernel;

 protected:
  framework::OpKernelType GetExpectedKernelType(
      const framework::ExecutionContext& ctx) const override {
    // choose cudnn kernel if the runtime supported.
    std::string data_format = ctx.Attr<std::string>("data_format");
    phi::DataLayout layout_ = phi::StringToDataLayout(data_format);
    auto input_data_type = OperatorWithKernel::IndicateVarDataType(
        ctx, framework::GradVarName("Out"));
    if (input_data_type == framework::proto::VarType::FP16) {
      if (!(platform::is_gpu_place(ctx.GetPlace()) ||
            platform::is_npu_place(ctx.GetPlace()) ||
            platform::is_xpu_place(ctx.GetPlace()) ||
            platform::is_mlu_place(ctx.GetPlace()) ||
            platform::is_custom_place(ctx.GetPlace())))
        PADDLE_THROW(platform::errors::InvalidArgument(
            "float16 can only be used on GPU/NPU/XPU/MLU and custom place"));
    }
    return framework::OpKernelType(input_data_type, ctx.GetPlace(), layout_);
  }
};

template <typename T>
class SoftmaxOpGradMaker : public framework::SingleGradOpMaker<T> {
 public:
  using framework::SingleGradOpMaker<T>::SingleGradOpMaker;

 protected:
  void Apply(GradOpPtr<T> op) const override {
    op->SetType("softmax_grad");

    op->SetInput("Out", this->Output("Out"));
    op->SetInput(framework::GradVarName("Out"), this->OutputGrad("Out"));

    op->SetAttrMap(this->Attrs());

    op->SetOutput(framework::GradVarName("X"), this->InputGrad("X"));
  }
};

DECLARE_INPLACE_OP_INFERER(SoftmaxInplaceInferer, {"X", "Out"});

}  // namespace operators
}  // namespace paddle

namespace ops = paddle::operators;

DECLARE_INFER_SHAPE_FUNCTOR(softmax,
                            SoftmaxInferShapeFunctor,
                            PD_INFER_META(phi::SoftmaxInferMeta));
REGISTER_OPERATOR(softmax,
                  ops::SoftmaxOp,
                  ops::SoftmaxOpMaker,
                  ops::SoftmaxOpInferVarType,
                  ops::SoftmaxOpGradMaker<paddle::framework::OpDesc>,
                  ops::SoftmaxOpGradMaker<paddle::imperative::OpBase>,
                  ops::SoftmaxInplaceInferer,
                  SoftmaxInferShapeFunctor);
DECLARE_INFER_SHAPE_FUNCTOR(softmax_grad,
                            SoftmaxGradInferShapeFunctor,
                            PD_INFER_META(phi::GeneralUnaryGradInferMeta));
REGISTER_OPERATOR(softmax_grad,
                  ops::SoftmaxOpGrad,
                  SoftmaxGradInferShapeFunctor);
