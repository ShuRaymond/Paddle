// Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#pragma once

#include <string>

#include "paddle/phi/core/dense_tensor.h"

namespace phi {

template <typename T, typename Context>
void SyncBatchNormKernel(const Context& dev_ctx,
                         const DenseTensor& x,
                         const DenseTensor& scale,
                         const DenseTensor& bias,
                         const DenseTensor& mean,
                         const DenseTensor& variance,
                         float momentum,
                         float epsilon,
                         const std::string& data_layout,
                         bool is_test,
                         bool use_global_stats,
                         bool trainable_statistics,
                         bool fuse_with_relu,
                         DenseTensor* y,
                         DenseTensor* mean_out,
                         DenseTensor* variance_out,
                         DenseTensor* saved_mean,
                         DenseTensor* saved_variance,
                         DenseTensor* reserve_space);
}  // namespace phi
