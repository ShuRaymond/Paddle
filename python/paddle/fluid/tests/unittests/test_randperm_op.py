#   Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import numpy as np
from op_test import OpTest
import paddle
import paddle.fluid.core as core
from paddle.static import program_guard, Program
from paddle.fluid.framework import _test_eager_guard
import os


def check_randperm_out(n, data_np):
    assert isinstance(data_np, np.ndarray), \
        "The input data_np should be np.ndarray."
    gt_sorted = np.arange(n)
    out_sorted = np.sort(data_np)
    return list(gt_sorted == out_sorted)


def error_msg(data_np):
    return "The sorted ground truth and sorted out should " + \
 "be equal, out = " + str(data_np)


def convert_dtype(dtype_str):
    dtype_str_list = ["int32", "int64", "float32", "float64"]
    dtype_num_list = [
        core.VarDesc.VarType.INT32, core.VarDesc.VarType.INT64,
        core.VarDesc.VarType.FP32, core.VarDesc.VarType.FP64
    ]
    assert dtype_str in dtype_str_list, dtype_str + \
        " should in " + str(dtype_str_list)
    return dtype_num_list[dtype_str_list.index(dtype_str)]


class TestRandpermOp(OpTest):
    """ Test randperm op."""

    def setUp(self):
        self.op_type = "randperm"
        self.python_api = paddle.randperm
        self.n = 200
        self.dtype = "int64"

        self.inputs = {}
        self.outputs = {"Out": np.zeros((self.n)).astype(self.dtype)}
        self.init_attrs()
        self.attrs = {
            "n": self.n,
            "dtype": convert_dtype(self.dtype),
        }

    def init_attrs(self):
        pass

    def test_check_output(self):
        self.check_output_customized(self.verify_output)

    def verify_output(self, outs):
        out_np = np.array(outs[0])
        self.assertTrue(check_randperm_out(self.n, out_np),
                        msg=error_msg(out_np))

    def test_eager(self):
        with _test_eager_guard():
            self.test_check_output()


class TestRandpermOpN(TestRandpermOp):

    def init_attrs(self):
        self.n = 10000


class TestRandpermOpInt32(TestRandpermOp):

    def init_attrs(self):
        self.dtype = "int32"


class TestRandpermOpFloat32(TestRandpermOp):

    def init_attrs(self):
        self.dtype = "float32"


class TestRandpermOpFloat64(TestRandpermOp):

    def init_attrs(self):
        self.dtype = "float64"


class TestRandpermOpError(unittest.TestCase):

    def test_errors(self):
        with program_guard(Program(), Program()):
            self.assertRaises(ValueError, paddle.randperm, -3)
            self.assertRaises(TypeError, paddle.randperm, 10, 'int8')


class TestRandpermAPI(unittest.TestCase):

    def test_out(self):
        n = 10
        place = paddle.CUDAPlace(
            0) if core.is_compiled_with_cuda() else paddle.CPUPlace()
        with program_guard(Program(), Program()):
            x1 = paddle.randperm(n)
            x2 = paddle.randperm(n, 'float32')

            exe = paddle.static.Executor(place)
            res = exe.run(fetch_list=[x1, x2])

            self.assertEqual(res[0].dtype, np.int64)
            self.assertEqual(res[1].dtype, np.float32)
            self.assertTrue(check_randperm_out(n, res[0]))
            self.assertTrue(check_randperm_out(n, res[1]))


class TestRandpermImperative(unittest.TestCase):

    def test_out(self):
        paddle.disable_static()
        n = 10
        for dtype in ['int32', np.int64, 'float32', 'float64']:
            data_p = paddle.randperm(n, dtype)
            data_np = data_p.numpy()
            self.assertTrue(check_randperm_out(n, data_np),
                            msg=error_msg(data_np))
        paddle.enable_static()


class TestRandpermEager(unittest.TestCase):

    def test_out(self):
        paddle.disable_static()
        n = 10
        with _test_eager_guard():
            for dtype in ['int32', np.int64, 'float32', 'float64']:
                data_p = paddle.randperm(n, dtype)
                data_np = data_p.numpy()
                self.assertTrue(check_randperm_out(n, data_np),
                                msg=error_msg(data_np))
        paddle.enable_static()


class TestRandomValue(unittest.TestCase):

    def test_fixed_random_number(self):
        # Test GPU Fixed random number, which is generated by 'curandStatePhilox4_32_10_t'
        if not paddle.is_compiled_with_cuda():
            return

        print("Test Fixed Random number on GPU------>")
        paddle.disable_static()
        paddle.set_device('gpu')
        paddle.seed(2021)

        x = paddle.randperm(30000, dtype='int32').numpy()
        expect = [
            24562, 8409, 9379, 10328, 20503, 18059, 9681, 21883, 11783, 27413
        ]
        self.assertTrue(np.array_equal(x[0:10], expect))
        expect = [
            29477, 27100, 9643, 16637, 8605, 16892, 27767, 2724, 1612, 13096
        ]
        self.assertTrue(np.array_equal(x[10000:10010], expect))
        expect = [
            298, 4104, 16479, 22714, 28684, 7510, 14667, 9950, 15940, 28343
        ]
        self.assertTrue(np.array_equal(x[20000:20010], expect))

        x = paddle.randperm(30000, dtype='int64').numpy()
        expect = [
            6587, 1909, 5525, 23001, 6488, 14981, 14355, 3083, 29561, 8171
        ]
        self.assertTrue(np.array_equal(x[0:10], expect))
        expect = [
            23460, 12394, 22501, 5427, 20185, 9100, 5127, 1651, 25806, 4818
        ]
        self.assertTrue(np.array_equal(x[10000:10010], expect))
        expect = [5829, 4508, 16193, 24836, 8526, 242, 9984, 9243, 1977, 11839]
        self.assertTrue(np.array_equal(x[20000:20010], expect))

        x = paddle.randperm(30000, dtype='float32').numpy()
        expect = [
            5154., 10537., 14362., 29843., 27185., 28399., 27561., 4144.,
            22906., 10705.
        ]
        self.assertTrue(np.array_equal(x[0:10], expect))
        expect = [
            1958., 18414., 20090., 21910., 22746., 27346., 22347., 3002., 4564.,
            26991.
        ]
        self.assertTrue(np.array_equal(x[10000:10010], expect))
        expect = [
            25580., 12606., 553., 16387., 29536., 4241., 20946., 16899., 16339.,
            4662.
        ]
        self.assertTrue(np.array_equal(x[20000:20010], expect))

        x = paddle.randperm(30000, dtype='float64').numpy()
        expect = [
            19051., 2449., 21940., 11121., 282., 7330., 13747., 24321., 21147.,
            9163.
        ]
        self.assertTrue(np.array_equal(x[0:10], expect))
        expect = [
            15483., 1315., 5723., 20954., 13251., 25539., 5074., 1823., 14945.,
            17624.
        ]
        self.assertTrue(np.array_equal(x[10000:10010], expect))
        expect = [
            10516., 2552., 29970., 5941., 986., 8007., 24805., 26753., 12202.,
            21404.
        ]
        self.assertTrue(np.array_equal(x[20000:20010], expect))
        paddle.enable_static()


if __name__ == "__main__":
    unittest.main()
