#   Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
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
import paddle.fluid.core as core
from paddle.fluid.op import Operator
import sys

sys.path.append('..')
from op_test import OpTest
import paddle
import paddle.fluid as fluid
import numpy
from test_momentum_op import calculate_momentum_by_numpy

paddle.enable_static()


class TestMomentumOp1(OpTest):
    def setUp(self):
        self.op_type = "momentum"
        self.dtype = np.float32
        self.init_dtype()
        self.set_mlu()

        param = np.random.random((123, 321)).astype(self.dtype)
        grad = np.random.random((123, 321)).astype(self.dtype)
        velocity = np.zeros((123, 321)).astype(self.dtype)
        learning_rate = np.array([0.001]).astype(np.float32)
        mu = 0.0001
        use_nesterov = False

        self.inputs = {
            'Param': param,
            'Grad': grad,
            'Velocity': velocity,
            'LearningRate': learning_rate,
        }

        self.attrs = {'mu': mu}

        param_out, velocity_out = calculate_momentum_by_numpy(
            param=param,
            grad=grad,
            mu=mu,
            velocity=velocity,
            use_nesterov=use_nesterov,
            learning_rate=learning_rate,
        )

        self.outputs = {'ParamOut': param_out, 'VelocityOut': velocity_out}

    def init_dtype(self):
        pass

    def set_mlu(self):
        self.place = paddle.device.MLUPlace(0)
        self.__class__.use_mlu = True

    def test_check_output(self):
        self.check_output_with_place(self.place)


class TestMomentumOpFp16(TestMomentumOp1):
    def init_dtype(self):
        self.dtype = np.float16

    def test_check_output(self):
        self.check_output_with_place(self.place, atol=1e-3)


class TestMomentumOp2(OpTest):
    '''Test Momentum with default values for attributes'''

    def setUp(self):
        self.op_type = "momentum"
        self.place = paddle.device.MLUPlace(0)
        self.__class__.use_mlu = True

        param = np.random.random((123, 321)).astype("float32")
        grad = np.random.random((123, 321)).astype("float32")
        velocity = np.zeros((123, 321)).astype("float32")
        learning_rate = np.array([0.001]).astype("float32")
        mu = 0.0001
        use_nesterov = True

        self.inputs = {
            'Param': param,
            'Grad': grad,
            'Velocity': velocity,
            'LearningRate': learning_rate,
        }

        self.attrs = {'mu': mu, 'use_nesterov': use_nesterov}

        param_out, velocity_out = calculate_momentum_by_numpy(
            param=param,
            grad=grad,
            mu=mu,
            velocity=velocity,
            use_nesterov=use_nesterov,
            learning_rate=learning_rate,
        )

        self.outputs = {'ParamOut': param_out, 'VelocityOut': velocity_out}

    def test_check_output(self):
        self.check_output_with_place(self.place)


class TestMomentumV2(unittest.TestCase):
    def test_momentum_dygraph(self):
        paddle.disable_static()
        value = np.arange(26).reshape(2, 13).astype("float32")
        a = paddle.to_tensor(value)
        linear = paddle.nn.Linear(13, 5)
        # This can be any optimizer supported by dygraph.
        adam = paddle.optimizer.Momentum(
            learning_rate=0.01, momentum=0.9, parameters=linear.parameters()
        )
        out = linear(a)
        out.backward()
        adam.step()
        adam.clear_gradients()

    def test_momentum(self):
        paddle.enable_static()
        place = fluid.MLUPlace(0)
        main = fluid.Program()
        with fluid.program_guard(main):
            x = fluid.layers.data(name='x', shape=[13], dtype='float32')
            y = fluid.layers.data(name='y', shape=[1], dtype='float32')
            y_predict = fluid.layers.fc(input=x, size=1, act=None)
            cost = fluid.layers.square_error_cost(input=y_predict, label=y)
            avg_cost = paddle.mean(cost)

            rms_optimizer = paddle.optimizer.Momentum(
                learning_rate=0.1, momentum=0.9
            )
            rms_optimizer.minimize(avg_cost)

            fetch_list = [avg_cost]
            train_reader = paddle.batch(
                paddle.dataset.uci_housing.train(), batch_size=1
            )
            feeder = fluid.DataFeeder(place=place, feed_list=[x, y])
            exe = fluid.Executor(place)
            exe.run(fluid.default_startup_program())
            for data in train_reader():
                exe.run(main, feed=feeder.feed(data), fetch_list=fetch_list)

    def test_raise_error(self):
        self.assertRaises(
            ValueError, paddle.optimizer.Momentum, learning_rate=None
        )
        self.assertRaises(ValueError, paddle.optimizer.Momentum, momentum=None)


class TestMomentumOpWithDecay(OpTest):
    def setUp(self):
        self.op_type = "momentum"
        self.place = paddle.device.MLUPlace(0)
        self.__class__.use_mlu = True
        self.dtype = np.float32
        self.use_nesterov = True
        self.regularization_method = 'l2_decay'
        self.regularization_coeff = 0.9
        self.init_config()

        param = np.random.random((123, 321)).astype(self.dtype)
        grad = np.random.random((123, 321)).astype(self.dtype)
        velocity = np.zeros((123, 321)).astype(self.dtype)
        learning_rate = np.array([0.001]).astype(np.float32)
        mu = 0.0001
        use_nesterov = self.use_nesterov
        regularization_method = self.regularization_method
        regularization_coeff = self.regularization_coeff

        self.inputs = {
            'Param': param,
            'Grad': grad,
            'Velocity': velocity,
            'LearningRate': learning_rate,
        }

        self.attrs = {
            'mu': mu,
            'use_nesterov': use_nesterov,
            'regularization_method': regularization_method,
            'regularization_coeff': regularization_coeff,
        }

        grad = grad + regularization_coeff * param

        param_out, velocity_out = calculate_momentum_by_numpy(
            param=param,
            grad=grad,
            mu=mu,
            velocity=velocity,
            use_nesterov=use_nesterov,
            learning_rate=learning_rate,
        )

        self.outputs = {'ParamOut': param_out, 'VelocityOut': velocity_out}

    def init_config(self):
        pass

    def test_check_output(self):
        paddle.enable_static()
        self.check_output_with_place(self.place)


class TestMomentumOpWithDecayFP16(TestMomentumOpWithDecay):
    def init_config(self):
        self.dtype = np.float16

    def test_check_output(self):
        self.check_output_with_place(self.place, atol=1e-3)


class TestMomentumOpWithDecay2(TestMomentumOpWithDecay):
    def init_config(self):
        self.use_nesterov = False


class TestMomentumOpWithDecayAPI(unittest.TestCase):
    def _test_momentum_dygraph_common(self, regularization):
        paddle.disable_static()
        inp = np.random.uniform(-0.1, 0.1, [10, 10]).astype("float32")
        linear = paddle.nn.Linear(10, 10)
        inp = paddle.to_tensor(inp)
        out = linear(inp)
        loss = paddle.mean(out)
        # This can be any optimizer supported by dygraph.
        momentum = paddle.fluid.contrib.optimizer.Momentum(
            learning_rate=0.01,
            momentum=0.9,
            parameter_list=linear.parameters(),
            regularization=regularization,
        )
        momentum.minimize(loss)

    def test_momentum_dygraph_1(self):
        self._test_momentum_dygraph_common(
            regularization=paddle.fluid.regularizer.L2Decay(
                regularization_coeff=0.1
            )
        )

    def test_momentum_static(self):
        paddle.enable_static()
        place = fluid.MLUPlace(0)
        main = fluid.Program()
        with fluid.program_guard(main):
            x = fluid.layers.data(name='x', shape=[13], dtype='float32')
            y = fluid.layers.data(name='y', shape=[1], dtype='float32')
            y_predict = fluid.layers.fc(input=x, size=1, act=None)
            cost = fluid.layers.square_error_cost(input=y_predict, label=y)
            avg_cost = paddle.mean(cost)

            momentum_optimizer = paddle.fluid.contrib.optimizer.Momentum(
                learning_rate=0.1, momentum=0.9
            )
            momentum_optimizer.minimize(avg_cost)

            fetch_list = [avg_cost]
            train_reader = paddle.batch(
                paddle.dataset.uci_housing.train(), batch_size=1
            )
            feeder = fluid.DataFeeder(place=place, feed_list=[x, y])
            exe = fluid.Executor(place)
            exe.run(fluid.default_startup_program())
            for data in train_reader():
                exe.run(main, feed=feeder.feed(data), fetch_list=fetch_list)


class TestFusedMomentumWithDecayAPI(unittest.TestCase):
    def get_program(self, weight_attr, bias_attr=False):
        main_program = paddle.static.Program()
        startup_program = paddle.static.Program()
        with paddle.static.program_guard(
            main_program=main_program, startup_program=startup_program
        ):
            x = paddle.static.data(name='x', shape=[10, 10])
            linear = paddle.nn.Linear(
                10, 10, weight_attr=weight_attr, bias_attr=bias_attr
            )
            out = linear(x)
            loss = paddle.mean(out)
            optimizer = paddle.optimizer.Momentum(
                learning_rate=0.01,
                momentum=0.9,
                weight_decay=paddle.regularizer.L2Decay(0.5),
            )
            optimizer.minimize(loss)
        return main_program

    def test_param_has_l2decay(self):
        paddle.enable_static()
        weight_attr = paddle.ParamAttr(
            name="weight",
            initializer=paddle.nn.initializer.Constant(value=0.5),
            regularizer=paddle.regularizer.L2Decay(0.1),
        )
        program = self.get_program(weight_attr, bias_attr=False)
        ops = program.global_block().ops

        self.assertEqual(ops[-1].attr('regularization_method'), 'l2_decay')
        self.assertEqual(ops[-1].attr('regularization_coeff'), np.float32(0.1))
        for i in range(len(ops)):
            self.assertTrue('sum' not in ops[i].type)
            self.assertTrue('scale' not in ops[i].type)

    def test_param_has_l1decay(self):
        paddle.enable_static()
        weight_attr = paddle.ParamAttr(
            name="weight",
            initializer=paddle.nn.initializer.Constant(value=0.5),
            regularizer=paddle.regularizer.L1Decay(0.1),
        )
        bias_attr = paddle.ParamAttr(
            name="bias",
            initializer=paddle.nn.initializer.Constant(value=0.0),
            regularizer=None,
        )
        program = self.get_program(weight_attr, bias_attr)
        ops = program.global_block().ops

        self.assertEqual(ops[-1].type, 'momentum')
        self.assertEqual(ops[-2].type, 'momentum')
        self.assertEqual(ops[-3].type, 'sum')
        self.assertEqual(ops[-4].type, 'scale')
        self.assertEqual(ops[-5].type, 'sign')
        self.assertEqual(ops[-6].type, 'matmul_v2_grad')
        if 'weight' in ops[-1].input('Param'):
            self.assertEqual(ops[-1].attr('regularization_method'), '')
            self.assertEqual(ops[-1].attr('regularization_coeff'), 0)
        if 'bias' in ops[-2].input('Param'):
            self.assertEqual(ops[-2].attr('regularization_method'), 'l2_decay')
            self.assertEqual(
                ops[-2].attr('regularization_coeff'), np.float32(0.5)
            )

    def test_param_has_no_regularizer(self):
        paddle.enable_static()
        program = self.get_program(weight_attr=None)
        ops = program.global_block().ops
        self.assertEqual(ops[-1].attr('regularization_method'), 'l2_decay')
        self.assertEqual(ops[-1].attr('regularization_coeff'), np.float32(0.5))
        for i in range(len(ops)):
            self.assertTrue('sum' not in ops[i].type)
            self.assertTrue('scale' not in ops[i].type)


class TestMomentumOpVsMomentumOpWithDecayAPI(unittest.TestCase):
    def __update_params(self, momentum, linear):
        for i in range(10):
            inp = paddle.full(
                shape=[2, 2], fill_value=i, dtype='float32'
            ).astype("float32")
            inp = paddle.to_tensor(inp)
            out = linear(inp)
            loss = paddle.mean(out)
            loss.backward()
            momentum.minimize(loss)
            linear.clear_gradients()

    def __test_vs(self, place=fluid.MLUPlace(0)):
        paddle.disable_static(place=place)

        linear_old = paddle.nn.Linear(
            2,
            2,
            weight_attr=paddle.nn.initializer.Constant(value=2.0),
            bias_attr=paddle.nn.initializer.Constant(value=2.0),
        )
        momentum_old = paddle.fluid.optimizer.Momentum(
            learning_rate=0.01,
            momentum=0.9,
            parameter_list=linear_old.parameters(),
            regularization=paddle.fluid.regularizer.L2Decay(
                regularization_coeff=0.1
            ),
        )
        self.__update_params(momentum=momentum_old, linear=linear_old)

        linear_new = paddle.nn.Linear(
            2,
            2,
            weight_attr=paddle.nn.initializer.Constant(value=2.0),
            bias_attr=paddle.nn.initializer.Constant(value=2.0),
        )
        momentum_new = paddle.fluid.contrib.optimizer.Momentum(
            learning_rate=0.01,
            momentum=0.9,
            parameter_list=linear_new.parameters(),
            regularization=paddle.fluid.regularizer.L2Decay(
                regularization_coeff=0.1
            ),
        )
        self.__update_params(momentum=momentum_new, linear=linear_new)

        self.assertEqual(
            (linear_old.weight.numpy() == linear_new.weight.numpy()).all(),
            True,
            'the param weight updated by two Momentum optimizers should equal',
        )

    def test_vs(self, place=fluid.MLUPlace(0)):
        places = [fluid.MLUPlace(0)]
        for place in places:
            self.__test_vs(place=place)


class TestMomentumV2Group(TestMomentumV2):
    def test_momentum_dygraph(self):
        paddle.disable_static()
        value = np.arange(26).reshape(2, 13).astype("float32")
        a = paddle.to_tensor(value)
        linear_1 = paddle.nn.Linear(13, 5)
        linear_2 = paddle.nn.Linear(5, 3)
        # This can be any optimizer supported by dygraph.
        adam = paddle.optimizer.Momentum(
            learning_rate=0.01,
            parameters=[
                {'params': linear_1.parameters()},
                {
                    'params': linear_2.parameters(),
                    'weight_decay': 0.001,
                    'learning_rate': 0.1,
                    'momentum': 0.99,
                },
            ],
            weight_decay=0.1,
            momentum=0.9,
        )
        out = linear_1(a)
        out = linear_2(out)
        out.backward()
        adam.step()
        adam.clear_gradients()


class TestMultiTensorMomentumDygraph(unittest.TestCase):
    def _momentum_optimize_dygraph(
        self,
        place,
        use_param_attr=False,
        use_param_group=False,
        use_amp=False,
        use_multi_tensor=False,
    ):
        paddle.disable_static()
        paddle.seed(10)
        paddle.set_device(place)
        input = paddle.randn((5, 5))
        weight_attr = paddle.ParamAttr(
            learning_rate=0.5,
            regularizer=paddle.regularizer.L2Decay(1.0),
            trainable=True,
        )
        if use_param_attr:
            model = paddle.nn.Linear(5, 5, weight_attr)
        else:
            model = paddle.nn.Linear(5, 5)
        if not use_param_group:
            optimizer = paddle.optimizer.Momentum(
                parameters=model.parameters(),
                use_multi_tensor=use_multi_tensor,
                multi_precision=use_amp,
            )
        else:
            optimizer = paddle.optimizer.Momentum(
                parameters=[
                    {
                        'params': model.parameters(),
                        'weight_decay': 0.001,
                        'learning_rate': 0.1,
                        'momentum': 0.99,
                    }
                ],
                use_multi_tensor=use_multi_tensor,
                multi_precision=use_amp,
            )
        for idx in range(5):
            if place == 'mlu' and use_amp == True:
                model = paddle.amp.decorate(models=model, level='O2')
                scaler = paddle.amp.GradScaler(init_loss_scaling=1024)
            if place == 'mlu' and use_amp == True:
                with paddle.amp.auto_cast(level='O2'):
                    output = model(input)
                    loss = paddle.mean(output)
                scaled = scaler.scale(loss)
                scaled.backward()
                scaler.step(optimizer)
                optimizer.clear_grad(set_to_zero=False)
            else:
                output = model(input)
                loss = paddle.mean(output)
                # This can be any optimizer supported by dygraph.
                loss.backward()
                optimizer.step()
                optimizer.clear_grad(set_to_zero=False)
        return output, model.parameters()

    def _get_places(self):
        places = ['mlu']
        return places

    def _check_with_place_amp(self, place, use_amp):
        output1, params1 = self._momentum_optimize_dygraph(
            place=place, use_amp=use_amp, use_multi_tensor=True
        )
        output2, params2 = self._momentum_optimize_dygraph(
            place=place, use_amp=use_amp, use_multi_tensor=False
        )
        np.testing.assert_allclose(output1, output2, rtol=1e-05)
        for idx in range(len(params1)):
            np.testing.assert_allclose(params1[idx], params2[idx], rtol=1e-05)

    def _check_with_param_arrt(self, place, use_amp):
        output1, params1 = self._momentum_optimize_dygraph(
            place=place,
            use_amp=use_amp,
            use_param_attr=True,
            use_multi_tensor=True,
        )
        output2, params2 = self._momentum_optimize_dygraph(
            place=place,
            use_amp=use_amp,
            use_param_attr=True,
            use_multi_tensor=False,
        )
        np.testing.assert_allclose(output1, output2, rtol=1e-05)
        for idx in range(len(params1)):
            np.testing.assert_allclose(params1[idx], params2[idx], rtol=1e-05)

    def _check_with_param_group(self, place, use_amp):
        output1, params1 = self._momentum_optimize_dygraph(
            place=place,
            use_amp=use_amp,
            use_param_group=True,
            use_multi_tensor=True,
        )
        output2, params2 = self._momentum_optimize_dygraph(
            place=place,
            use_amp=use_amp,
            use_param_group=True,
            use_multi_tensor=False,
        )
        np.testing.assert_allclose(output1, output2, rtol=1e-05)
        for idx in range(len(params1)):
            np.testing.assert_allclose(params1[idx], params2[idx], rtol=1e-05)

    def test_main(self):
        for place in self._get_places():
            # use_amp_list = [True, False]
            use_amp_list = [False]
            for use_amp in use_amp_list:
                self._check_with_place_amp(place, use_amp)
                self._check_with_param_arrt(place, use_amp)
                self._check_with_param_group(place, use_amp)


class TestMultiTensorMomentumStatic(unittest.TestCase):
    def _momentum_optimize_static(
        self, place, use_amp=False, use_multi_tensor=False
    ):
        paddle.enable_static()
        paddle.seed(10)
        np.random.seed(10)
        if place == 'cpu':
            use_amp = False
        exe = paddle.static.Executor(place=paddle.device.MLUPlace(0))
        train_program = paddle.static.Program()
        startup_program = paddle.static.Program()
        optimizer = paddle.optimizer.Momentum(
            multi_precision=use_amp, use_multi_tensor=use_multi_tensor
        )
        if use_amp:
            optimizer = paddle.static.amp.decorate(
                optimizer,
                init_loss_scaling=128.0,
                use_dynamic_loss_scaling=True,
                use_pure_fp16=True,
                use_fp16_guard=False,
            )
        with paddle.static.program_guard(train_program, startup_program):
            if use_amp:
                data = paddle.static.data(
                    shape=[2, 2], name='X', dtype='float16'
                )
            else:
                data = paddle.static.data(
                    shape=[2, 2], name='X', dtype='float32'
                )
            hidden = paddle.static.nn.fc(x=data, size=10)
            loss = paddle.mean(hidden)
            optimizer.minimize(loss)
        exe.run(startup_program)
        if use_amp:
            optimizer.amp_init(place=place, scope=paddle.static.global_scope())
            x = numpy.random.random(size=(2, 2)).astype('float16')
        else:
            x = numpy.random.random(size=(2, 2)).astype('float32')
        out = []
        for idx in range(5):
            (loss_data,) = exe.run(
                train_program, feed={"X": x}, fetch_list=[loss.name]
            )
            out.append(loss_data)
        return out

    def _get_places(self):
        places = ['mlu']
        return places

    def _check_with_place_amp(self, place, use_amp):
        output1 = self._momentum_optimize_static(
            place=place, use_amp=use_amp, use_multi_tensor=True
        )
        output2 = self._momentum_optimize_static(
            place=place, use_amp=use_amp, use_multi_tensor=False
        )
        for idx in range(len(output1)):
            np.testing.assert_allclose(output1[idx], output2[idx], rtol=1e-05)

    def test_main(self):
        for place in self._get_places():
            # use_amp_list = [True, False]
            use_amp_list = [False]
            for use_amp in use_amp_list:
                self._check_with_place_amp(place, use_amp)


if __name__ == "__main__":
    unittest.main()
