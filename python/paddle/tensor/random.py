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

# TODO: define random functions

from ..framework import core
from ..framework import convert_np_dtype_to_dtype_, dygraph_only
from ..framework import LayerHelper
from ..fluid.data_feeder import (
    check_variable_and_dtype,
    check_type,
    check_dtype,
    check_shape,
)
from ..fluid.layers import utils
import paddle
from paddle import _C_ops, _legacy_C_ops
from paddle.static import Variable
from paddle.fluid.framework import (
    in_dygraph_mode,
    _in_legacy_dygraph,
    _current_expected_place,
)

__all__ = []


def bernoulli(x, name=None):
    r"""

    For each element :math:`x_i` in input ``x``, take a sample from the Bernoulli distribution, also called two-point distribution, with success probability :math:`x_i`. The Bernoulli distribution with success probability :math:`x_i` is a discrete probability distribution with probability mass function

    .. math::
        p(y)=\begin{cases}
            x_i,&y=1\\
            1-x_i,&y=0
        \end{cases}.

    Args:
        x (Tensor): The input Tensor, it's data type should be float32, float64.
        name (str, optional): For details, please refer to :ref:`api_guide_Name`. Generally, no setting is required. Default: None.

    Returns:
        Tensor: A Tensor filled samples from Bernoulli distribution, whose shape and dtype are same as ``x``.

    Examples:
        .. code-block:: python

            import paddle

            paddle.set_device('cpu')  # on CPU device
            paddle.seed(100)

            x = paddle.rand([2,3])
            print(x)
            # [[0.55355281, 0.20714243, 0.01162981],
            #  [0.51577556, 0.36369765, 0.26091650]]

            out = paddle.bernoulli(x)
            print(out)
            # [[1., 0., 1.],
            #  [0., 1., 0.]]

    """

    if in_dygraph_mode():
        return _C_ops.bernoulli(x)

    if _in_legacy_dygraph():
        return _legacy_C_ops.bernoulli(x)

    check_variable_and_dtype(x, "x", ["float32", "float64"], "bernoulli")

    helper = LayerHelper("randint", **locals())
    out = helper.create_variable_for_type_inference(
        dtype=x.dtype
    )  # maybe set out to int32 ?
    helper.append_op(
        type='bernoulli', inputs={"X": x}, outputs={'Out': out}, attrs={}
    )
    out.stop_gradient = True
    return out


def poisson(x, name=None):
    r"""
    Returns a tensor filled with random number from a Poisson Distribution.

    .. math::

        out_i \sim Poisson (lambda = x_i)

    Args:
        x(Tensor):  A tensor with rate parameter of poisson Distribution. The data type
            should be float32, float64.
        name(str, optional): The default value is None. Normally there is no
            need for user to set this property. For more information, please
            refer to :ref:`api_guide_Name`.
    Returns:
        Tensor: A Tensor filled with random number with the same shape and dtype as ``x``.

    Examples:
        .. code-block:: python

            import paddle
            paddle.set_device('cpu')
            paddle.seed(100)

            x = paddle.uniform([2,3], min=1.0, max=5.0)
            out = paddle.poisson(x)
            #[[2., 5., 0.],
            # [5., 1., 3.]]

    """
    if in_dygraph_mode():
        return _C_ops.poisson(x)

    if paddle.in_dynamic_mode():
        return _legacy_C_ops.poisson(x)

    check_variable_and_dtype(x, "x", ["float32", "float64"], "poisson")

    helper = LayerHelper("poisson", **locals())
    out = helper.create_variable_for_type_inference(dtype=x.dtype)
    helper.append_op(
        type='poisson', inputs={'X': x}, outputs={'Out': out}, attrs={}
    )
    return out


def multinomial(x, num_samples=1, replacement=False, name=None):
    """
    Returns a Tensor filled with random values sampled from a Multinomical
    distribution. The input ``x`` is a tensor with probabilities for generating the
    random number. Each element in ``x`` should be larger or equal to 0, but not all
    0. ``replacement`` indicates whether it is a replaceable sample. If ``replacement``
    is True, a category can be sampled more than once.

    Args:
        x(Tensor):  A tensor with probabilities for generating the random number. The data type
            should be float32, float64.
        num_samples(int, optional): Number of samples, default is 1.
        replacement(bool, optional): Whether it is a replaceable sample, default is False.
        name(str, optional): The default value is None. Normally there is no
            need for user to set this property. For more information, please
            refer to :ref:`api_guide_Name`.
    Returns:
        Tensor: A Tensor filled with sampled category index after ``num_samples`` times samples.

    Examples:
        .. code-block:: python

            import paddle

            paddle.seed(100) # on CPU device
            x = paddle.rand([2,4])
            print(x)
            # [[0.5535528  0.20714243 0.01162981 0.51577556]
            # [0.36369765 0.2609165  0.18905126 0.5621971 ]]

            paddle.seed(200) # on CPU device
            out1 = paddle.multinomial(x, num_samples=5, replacement=True)
            print(out1)
            # [[3 3 0 0 0]
            # [3 3 3 1 0]]

            # out2 = paddle.multinomial(x, num_samples=5)
            # InvalidArgumentError: When replacement is False, number of samples
            #  should be less than non-zero categories

            paddle.seed(300) # on CPU device
            out3 = paddle.multinomial(x, num_samples=3)
            print(out3)
            # [[3 0 1]
            # [3 1 0]]

    """

    assert (
        not core.is_compiled_with_rocm()
    ), "multinomial op is not supported on ROCM yet."

    if in_dygraph_mode():
        return _C_ops.multinomial(x, num_samples, replacement)

    if _in_legacy_dygraph():
        return _legacy_C_ops.multinomial(
            x, 'num_samples', num_samples, 'replacement', replacement
        )

    check_variable_and_dtype(x, "x", ["float32", "float64"], "multinomial")

    helper = LayerHelper("multinomial", **locals())
    out = helper.create_variable_for_type_inference(
        dtype=convert_np_dtype_to_dtype_('int64')
    )
    helper.append_op(
        type='multinomial',
        inputs={"X": x},
        outputs={'Out': out},
        attrs={'num_samples': num_samples, 'replacement': replacement},
    )
    out.stop_gradient = True
    return out


def gaussian(shape, mean=0.0, std=1.0, dtype=None, name=None):
    """
    Returns a Tensor filled with random values sampled from a Gaussian
    distribution, with ``shape`` and ``dtype``.

    Args:
        shape (list|tuple|Tensor): The shape of the output Tensor. If ``shape``
            is a list or tuple, the elements of it should be integers or Tensors
            (with the shape [1], and the data type int32 or int64). If ``shape``
            is a Tensor, it should be a 1-D Tensor(with the data type int32 or
            int64).
        mean (float|int, optional): Mean of the output tensor, default is 0.0.
        std (float|int, optional): Standard deviation of the output tensor, default
            is 1.0.
        seed (int, optional): Random seed of generator.
        dtype (str|np.dtype, optional): The data type of the output Tensor.
            Supported data types: float32, float64.
            Default is None, use global default dtype (see ``get_default_dtype``
            for details).
        name (str, optional): Name for the operation (optional, default is None). For more information, please refer to :ref:`api_guide_Name`.

    Returns:
        Tensor: A Tensor filled with random values sampled from a Gaussian
        distribution, with ``shape`` and ``dtype``.
    """
    op_type_for_check = 'gaussian/standard_normal/randn/normal'
    seed = 0

    if dtype is None:
        dtype = paddle.framework.get_default_dtype()
        if dtype not in ['float32', 'float64']:
            raise TypeError(
                "{} only supports [float32, float64], but the default dtype is {}".format(
                    op_type_for_check, dtype
                )
            )
    if not isinstance(dtype, core.VarDesc.VarType):
        dtype = convert_np_dtype_to_dtype_(dtype)

    if in_dygraph_mode():
        shape = utils.convert_shape_to_list(shape)
        place = _current_expected_place()
        return _C_ops.gaussian(
            shape, float(mean), float(std), seed, dtype, place
        )

    if _in_legacy_dygraph():
        shape = utils.convert_shape_to_list(shape)
        return _legacy_C_ops.gaussian_random(
            'shape',
            shape,
            'mean',
            float(mean),
            'std',
            float(std),
            'seed',
            seed,
            'dtype',
            dtype,
        )

    check_shape(shape, op_type_for_check)
    check_dtype(dtype, 'dtype', ['float32', 'float64'], op_type_for_check)

    inputs = {}
    attrs = {
        'mean': mean,
        'std': std,
        'seed': seed,
        'dtype': dtype,
        'use_mkldnn': False,
    }
    utils.get_shape_tensor_inputs(
        inputs=inputs, attrs=attrs, shape=shape, op_type=op_type_for_check
    )

    helper = LayerHelper('gaussian', **locals())
    out = helper.create_variable_for_type_inference(dtype)
    helper.append_op(
        type='gaussian_random', inputs=inputs, outputs={'Out': out}, attrs=attrs
    )
    out.stop_gradient = True
    return out


def standard_normal(shape, dtype=None, name=None):
    """
    Returns a Tensor filled with random values sampled from a standard
    normal distribution with mean 0 and standard deviation 1, with ``shape``
    and ``dtype``.

    Args:
        shape (list|tuple|Tensor): The shape of the output Tensor. If ``shape``
            is a list or tuple, the elements of it should be integers or Tensors
            (with the shape [1], and the data type int32 or int64). If ``shape``
            is a Tensor, it should be a 1-D Tensor(with the data type int32 or
            int64).
        dtype (str|np.dtype, optional): The data type of the output Tensor.
            Supported data types: float32, float64.
            Default is None, use global default dtype (see ``get_default_dtype``
            for details).
        name (str, optional): Name for the operation (optional, default is None).
            For more information, please refer to :ref:`api_guide_Name`.

    Returns:
        Tensor: A Tensor filled with random values sampled from a standard
        normal distribution with mean 0 and standard deviation 1, with
        ``shape`` and ``dtype``.

    Examples:
        .. code-block:: python

            import paddle

            # example 1: attr shape is a list which doesn't contain Tensor.
            out1 = paddle.standard_normal(shape=[2, 3])
            # [[-2.923464  ,  0.11934398, -0.51249987],  # random
            #  [ 0.39632758,  0.08177969,  0.2692008 ]]  # random

            # example 2: attr shape is a list which contains Tensor.
            dim1 = paddle.to_tensor([2], 'int64')
            dim2 = paddle.to_tensor([3], 'int32')
            out2 = paddle.standard_normal(shape=[dim1, dim2, 2])
            # [[[-2.8852394 , -0.25898588],  # random
            #   [-0.47420555,  0.17683524],  # random
            #   [-0.7989969 ,  0.00754541]],  # random
            #  [[ 0.85201347,  0.32320443],  # random
            #   [ 1.1399018 ,  0.48336947],  # random
            #   [ 0.8086993 ,  0.6868893 ]]]  # random

            # example 3: attr shape is a Tensor, the data type must be int64 or int32.
            shape_tensor = paddle.to_tensor([2, 3])
            out3 = paddle.standard_normal(shape_tensor)
            # [[-2.878077 ,  0.17099959,  0.05111201]  # random
            #  [-0.3761474, -1.044801  ,  1.1870178 ]]  # random

    """
    return gaussian(shape=shape, mean=0.0, std=1.0, dtype=dtype, name=name)


def randn(shape, dtype=None, name=None):
    """
    Returns a Tensor filled with random values sampled from a standard
    normal distribution with mean 0 and standard deviation 1, with ``shape``
    and ``dtype``.

    Args:
        shape (list|tuple|Tensor): The shape of the output Tensor. If ``shape``
            is a list or tuple, the elements of it should be integers or Tensors
            (with the shape [1], and the data type int32 or int64). If ``shape``
            is a Tensor, it should be a 1-D Tensor(with the data type int32 or
            int64).
        dtype (str|np.dtype, optional): The data type of the output Tensor.
            Supported data types: float32, float64.
            Default is None, use global default dtype (see ``get_default_dtype``
            for details).
        name (str, optional): Name for the operation (optional, default is None).
            For more information, please refer to :ref:`api_guide_Name`.

    Returns:
        Tensor: A Tensor filled with random values sampled from a standard
        normal distribution with mean 0 and standard deviation 1, with
        ``shape`` and ``dtype``.

    Examples:
        .. code-block:: python

            import paddle

            # example 1: attr shape is a list which doesn't contain Tensor.
            out1 = paddle.randn(shape=[2, 3])
            # [[-2.923464  ,  0.11934398, -0.51249987],  # random
            #  [ 0.39632758,  0.08177969,  0.2692008 ]]  # random

            # example 2: attr shape is a list which contains Tensor.
            dim1 = paddle.to_tensor([2], 'int64')
            dim2 = paddle.to_tensor([3], 'int32')
            out2 = paddle.randn(shape=[dim1, dim2, 2])
            # [[[-2.8852394 , -0.25898588],  # random
            #   [-0.47420555,  0.17683524],  # random
            #   [-0.7989969 ,  0.00754541]],  # random
            #  [[ 0.85201347,  0.32320443],  # random
            #   [ 1.1399018 ,  0.48336947],  # random
            #   [ 0.8086993 ,  0.6868893 ]]]  # random

            # example 3: attr shape is a Tensor, the data type must be int64 or int32.
            shape_tensor = paddle.to_tensor([2, 3])
            out3 = paddle.randn(shape_tensor)
            # [[-2.878077 ,  0.17099959,  0.05111201]  # random
            #  [-0.3761474, -1.044801  ,  1.1870178 ]]  # random
    """
    return standard_normal(shape, dtype, name)


def normal(mean=0.0, std=1.0, shape=None, name=None):
    """
    Returns a Tensor filled with random values sampled from a normal
    distribution with ``mean`` and ``std`` (standard deviation) .

    If ``mean`` is a Tensor, the output Tensor has the same shape and data type as ``mean``.
    If ``mean`` is not a Tensor and ``std`` is a Tensor, the output Tensor has the same shape and data type as ``std``.
    If ``mean`` and ``std`` are not a Tensor, the output Tensor has the same shape as ``shape``, with data type float32.

    If ``mean`` and ``std`` are Tensor, the num of elements of ``mean`` and ``std`` should be the same.

    Args:
        mean (float|Tensor, optional): The mean of the output Tensor's normal distribution.
            If ``mean`` is float, all elements of the output Tensor shared the same mean.
            If ``mean`` is a Tensor(data type supports float32, float64), it has per-element means.
            Default is 0.0
        std (float|Tensor, optional): The  standard deviation of the output Tensor's normal distribution.
            If ``std`` is float, all elements of the output Tensor shared the same standard deviation.
            If ``std`` is a Tensor(data type supports float32, float64), it has per-element standard deviations.
            Defaule is 1.0
        shape (list|tuple|Tensor, optional): The shape of the output Tensor. If ``shape``
            is a list or tuple, the elements of it should be integers or Tensors
            (with the shape [1], and the data type int32 or int64). If ``shape``
            is a Tensor, it should be a 1-D Tensor(with the data type int32 or
            int64). If ``mean`` or ``std`` is a Tensor, the shape of the output
            Tensor is the same as ``mean`` or ``std`` , attr ``shape`` is ignored.
            Default is None
        name (str, optional): Name for the operation (optional, default is None).
            For more information, please refer to :ref:`api_guide_Name`.

    Returns:
        A Tensor filled with random values sampled from a normal distribution with ``mean`` and ``std`` .

    Examples:
        .. code-block:: python

            import paddle

            out1 = paddle.normal(shape=[2, 3])
            # [[ 0.17501129  0.32364586  1.561118  ]  # random
            #  [-1.7232178   1.1545963  -0.76156676]]  # random

            mean_tensor = paddle.to_tensor([1.0, 2.0, 3.0])
            out2 = paddle.normal(mean=mean_tensor)
            # [ 0.18644847 -1.19434458  3.93694787]  # random

            std_tensor = paddle.to_tensor([1.0, 2.0, 3.0])
            out3 = paddle.normal(mean=mean_tensor, std=std_tensor)
            # [1.00780561 3.78457445 5.81058198]  # random

    """
    if not paddle.in_dynamic_mode():
        check_type(mean, 'mean', (int, float, Variable), 'normal')
        check_type(std, 'std', (int, float, Variable), 'normal')
        if isinstance(mean, Variable):
            check_dtype(
                mean.dtype,
                'mean',
                ['float32', 'float64'],
                'normal',
                "If mean is Tensor, it's data type only support float32, float64.",
            )
        if isinstance(std, Variable):
            check_dtype(
                std.dtype,
                'std',
                ['float32', 'float64'],
                'normal',
                "If std is Tensor, it's data type only support float32, float64.",
            )
        if shape is not None:
            check_shape(shape, 'normal')

    if isinstance(mean, Variable):
        if isinstance(std, Variable):
            if std.dtype != mean.dtype:
                std = paddle.cast(std, mean.dtype)
            mean_shape = paddle.shape(mean)
            std = paddle.reshape(std, mean_shape)
        else:
            std = float(std)
        out = standard_normal(paddle.shape(mean), mean.dtype, name)
    elif isinstance(std, Variable):
        mean = float(mean)
        out = standard_normal(paddle.shape(std), std.dtype, name)
    else:
        return gaussian(shape=shape, mean=mean, std=std, name=name)

    out = out * std + mean
    if not paddle.in_dynamic_mode():
        out.stop_grediant = True
    return out


def uniform(shape, dtype=None, min=-1.0, max=1.0, seed=0, name=None):
    """
    Returns a Tensor filled with random values sampled from a uniform
    distribution in the range [``min``, ``max``), with ``shape`` and ``dtype``.

    Examples:

    .. code-block:: text

        Input:
          shape = [1, 2]
        Output:
          result=[[0.8505902, 0.8397286]]

    Args:
        shape(list|tuple|Tensor): The shape of the output Tensor. If ``shape``
            is a list or tuple, the elements of it should be integers or Tensors
            (with the shape [1], and the data type int32 or int64). If ``shape``
            is a Tensor, it should be a 1-D Tensor(with the data type int32 or
            int64).
        dtype(str|np.dtype, optional): The data type of the output Tensor.
            Supported data types: float32, float64.
            Default is None, use global default dtype (see ``get_default_dtype``
            for details).
        min(float|int, optional): The lower bound on the range of random values
            to generate, ``min`` is included in the range. Default is -1.0.
        max(float|int, optional): The upper bound on the range of random values
            to generate, ``max`` is excluded in the range. Default is 1.0.
        seed(int, optional): Random seed used for generating samples. If seed is 0,
            it will use the seed of the global default generator (which can be set by paddle.seed).
            Note that if seed is not 0, this operator will always generate the same random numbers every
            time. Default is 0.
        name(str, optional): Name for the operation (optional, default is None).
            For more information, please refer to :ref:`api_guide_Name`.

    Returns:
        Tensor: A Tensor filled with random values sampled from a uniform
        distribution in the range [``min``, ``max``), with ``shape`` and ``dtype``.

    Examples:
        .. code-block:: python
          :name: code-example1

            import paddle

            # example 1:
            # attr shape is a list which doesn't contain Tensor.
            out1 = paddle.uniform(shape=[3, 4])
            # [[ 0.84524226,  0.6921872,   0.56528175,  0.71690357], # random
            #  [-0.34646994, -0.45116323, -0.09902662, -0.11397249], # random
            #  [ 0.433519,    0.39483607, -0.8660099,   0.83664286]] # random

            # example 2:
            # attr shape is a list which contains Tensor.
            dim1 = paddle.to_tensor([2], 'int64')
            dim2 = paddle.to_tensor([3], 'int32')
            out2 = paddle.uniform(shape=[dim1, dim2])
            # [[-0.9951253,   0.30757582, 0.9899647 ], # random
            #  [ 0.5864527,   0.6607096,  -0.8886161]] # random

            # example 3:
            # attr shape is a Tensor, the data type must be int64 or int32.
            shape_tensor = paddle.to_tensor([2, 3])
            out3 = paddle.uniform(shape_tensor)
            # [[-0.8517412,  -0.4006908,   0.2551912 ], # random
            #  [ 0.3364414,   0.36278176, -0.16085452]] # random
    """
    if dtype is None:
        dtype = paddle.framework.get_default_dtype()
        if dtype not in ['float32', 'float64']:
            raise TypeError(
                "uniform/rand only supports [float32, float64], but the default dtype is {}".format(
                    dtype
                )
            )

    if not isinstance(dtype, core.VarDesc.VarType):
        dtype = convert_np_dtype_to_dtype_(dtype)

    if in_dygraph_mode():
        shape = utils.convert_shape_to_list(shape)
        return _C_ops.uniform(
            shape,
            dtype,
            float(min),
            float(max),
            seed,
            _current_expected_place(),
        )

    if _in_legacy_dygraph():
        shape = utils.convert_shape_to_list(shape)
        return _legacy_C_ops.uniform_random(
            'shape',
            shape,
            'min',
            float(min),
            'max',
            float(max),
            'seed',
            seed,
            'dtype',
            dtype,
        )

    check_type(shape, 'shape', (list, tuple, Variable), 'uniform/rand')
    check_dtype(dtype, 'dtype', ('float32', 'float64'), 'uniform/rand')
    check_type(min, 'min', (float, int, Variable), 'uniform/rand')
    check_type(max, 'max', (float, int, Variable), 'uniform/rand')

    inputs = dict()
    attrs = {'seed': seed, 'min': min, 'max': max, 'dtype': dtype}
    utils.get_shape_tensor_inputs(
        inputs=inputs, attrs=attrs, shape=shape, op_type='uniform/rand'
    )

    helper = LayerHelper("uniform", **locals())
    out = helper.create_variable_for_type_inference(dtype)
    helper.append_op(
        type="uniform_random", inputs=inputs, attrs=attrs, outputs={"Out": out}
    )
    out.stop_gradient = True
    return out


@dygraph_only
def uniform_(x, min=-1.0, max=1.0, seed=0, name=None):
    """
    This is the inplace version of OP ``uniform``, which returns a Tensor filled
    with random values sampled from a uniform distribution. The output Tensor will
    be inplaced with input ``x``. Please refer to :ref:`api_tensor_uniform`.

    Args:
        x(Tensor): The input tensor to be filled with random values.
        min(float|int, optional): The lower bound on the range of random values
            to generate, ``min`` is included in the range. Default is -1.0.
        max(float|int, optional): The upper bound on the range of random values
            to generate, ``max`` is excluded in the range. Default is 1.0.
        seed(int, optional): Random seed used for generating samples. If seed is 0,
            it will use the seed of the global default generator (which can be set by paddle.seed).
            Note that if seed is not 0, this operator will always generate the same random numbers every
            time. Default is 0.
        name(str, optional): The default value is None. Normally there is no
            need for user to set this property. For more information, please
            refer to :ref:`api_guide_Name`.
    Returns:
        Tensor: The input tensor x filled with random values sampled from a uniform
        distribution in the range [``min``, ``max``).
    Examples:
        .. code-block:: python

            import paddle
            # example:
            x = paddle.ones(shape=[3, 4])
            x.uniform_()
            print(x)
            # [[ 0.84524226,  0.6921872,   0.56528175,  0.71690357], # random
            #  [-0.34646994, -0.45116323, -0.09902662, -0.11397249], # random
            #  [ 0.433519,    0.39483607, -0.8660099,   0.83664286]] # random
    """
    if in_dygraph_mode():
        return _C_ops.uniform_inplace_(x, min, max, seed, 0, 0, 1.0)
    else:
        return _legacy_C_ops.uniform_random_inplace_(
            x, 'min', min, 'max', max, 'seed', seed
        )


def randint(low=0, high=None, shape=[1], dtype=None, name=None):
    """
    Returns a Tensor filled with random integers from a discrete uniform
    distribution in the range [``low``, ``high``), with ``shape`` and ``dtype``.
    If ``high`` is None (the default), the range is [0, ``low``).

    Args:
        low (int, optional): The lower bound on the range of random values to generate.
            The ``low`` is included in the range. If ``high`` is None, the
            range is [0, ``low``). Default is 0.
        high (int, optional): The upper bound on the range of random values to
            generate, the ``high`` is excluded in the range. Default is None
            (see above for behavior if high = None). Default is None.
        shape (list|tuple|Tensor, optional): The shape of the output Tensor. If ``shape``
            is a list or tuple, the elements of it should be integers or Tensors
            (with the shape [1], and the data type int32 or int64). If ``shape``
            is a Tensor, it should be a 1-D Tensor(with the data type int32 or
            int64). Default is [1].
        dtype (str|np.dtype, optional): The data type of the
            output tensor. Supported data types: int32, int64. If ``dytpe``
            is None, the data type is int64. Default is None.
        name (str, optional): The default value is None.  Normally there is no
            need for user to set this property.  For more information, please
            refer to :ref:`api_guide_Name`.

    Returns:
        Tensor: A Tensor filled with random integers from a discrete uniform
        distribution in the range [``low``, ``high``), with ``shape`` and ``dtype``.

    Examples:
        .. code-block:: python

            import paddle

            # example 1:
            # attr shape is a list which doesn't contain Tensor.
            out1 = paddle.randint(low=-5, high=5, shape=[3])
            # [0, -3, 2]  # random

            # example 2:
            # attr shape is a list which contains Tensor.
            dim1 = paddle.to_tensor([2], 'int64')
            dim2 = paddle.to_tensor([3], 'int32')
            out2 = paddle.randint(low=-5, high=5, shape=[dim1, dim2])
            # [[0, -1, -3],  # random
            #  [4, -2,  0]]  # random

            # example 3:
            # attr shape is a Tensor
            shape_tensor = paddle.to_tensor(3)
            out3 = paddle.randint(low=-5, high=5, shape=shape_tensor)
            # [-2, 2, 3]  # random

            # example 4:
            # data type is int32
            out4 = paddle.randint(low=-5, high=5, shape=[3], dtype='int32')
            # [-5, 4, -4]  # random

            # example 5:
            # Input only one parameter
            # low=0, high=10, shape=[1], dtype='int64'
            out5 = paddle.randint(10)
            # [7]  # random

    """
    if high is None:
        if low <= 0:
            raise ValueError(
                "If high is None, low must be greater than 0, but received low = {0}.".format(
                    low
                )
            )
        high = low
        low = 0
    if dtype is None:
        dtype = 'int64'
    if not isinstance(dtype, core.VarDesc.VarType):
        dtype = convert_np_dtype_to_dtype_(dtype)

    if in_dygraph_mode():
        shape = utils.convert_shape_to_list(shape)
        place = _current_expected_place()
        return _C_ops.randint(low, high, shape, dtype, place)
    if _in_legacy_dygraph():
        shape = utils.convert_shape_to_list(shape)
        return _legacy_C_ops.randint(
            'shape', shape, 'low', low, 'high', high, 'seed', 0, 'dtype', dtype
        )

    check_shape(shape, 'randint')
    check_dtype(dtype, 'dtype', ['int32', 'int64'], 'randint')
    if low >= high:
        raise ValueError(
            "randint's low must less then high, but received low = {0}, "
            "high = {1}".format(low, high)
        )

    inputs = dict()
    attrs = {'low': low, 'high': high, 'seed': 0, 'dtype': dtype}
    utils.get_shape_tensor_inputs(
        inputs=inputs, attrs=attrs, shape=shape, op_type='randint'
    )

    helper = LayerHelper("randint", **locals())
    out = helper.create_variable_for_type_inference(dtype=dtype)
    helper.append_op(
        type='randint', inputs=inputs, outputs={'Out': out}, attrs=attrs
    )
    out.stop_gradient = True
    return out


def randint_like(x, low=0, high=None, dtype=None, name=None):
    """
    Returns a Tensor filled with random integers from a discrete uniform
    distribution in the range [``low``, ``high``), with the same shape as ``x``.
    (use ``dtype`` if ``dtype`` is not None)
    If ``high`` is None (the default), the range is [0, ``low``).

    Args:
        x (Tensor): The input tensor which specifies shape. The dtype of ``x``
            can be bool, int32, int64, float16, float32, float64.
        low (int): The lower bound on the range of random values to generate.
            The ``low`` is included in the range. If ``high`` is None, the
            range is [0, ``low``). Default is 0.
        high (int, optional): The upper bound on the range of random values to
            generate, the ``high`` is excluded in the range. Default is None
            (see above for behavior if high = None). Default is None.
        dtype (str|np.dtype, optional): The data type of the
            output tensor. Supported data types: bool, int32, int64, float16,
            float32, float64. If ``dytpe`` is None, the data type is the
            same as x's data type. Default is None.
        name (str, optional): The default value is None.  Normally there is no
            need for user to set this property.  For more information, please
            refer to :ref:`api_guide_Name`.

    Returns:
        Tensor: A Tensor filled with random integers from a discrete uniform
        distribution in the range [``low``, ``high``), with ``shape`` and ``dtype``.

    Examples:
        .. code-block:: python

            import paddle

            # example 1:
            # dtype is None and the dtype of x is float16
            x = paddle.zeros((1,2)).astype("float16")
            out1 = paddle.randint_like(x, low=-5, high=5)
            print(out1)
            print(out1.dtype)
            # [[0, -3]]  # random
            # paddle.float16

            # example 2:
            # dtype is None and the dtype of x is float32
            x = paddle.zeros((1,2)).astype("float32")
            out2 = paddle.randint_like(x, low=-5, high=5)
            print(out2)
            print(out2.dtype)
            # [[0, -3]]  # random
            # paddle.float32

            # example 3:
            # dtype is None and the dtype of x is float64
            x = paddle.zeros((1,2)).astype("float64")
            out3 = paddle.randint_like(x, low=-5, high=5)
            print(out3)
            print(out3.dtype)
            # [[0, -3]]  # random
            # paddle.float64

            # example 4:
            # dtype is None and the dtype of x is int32
            x = paddle.zeros((1,2)).astype("int32")
            out4 = paddle.randint_like(x, low=-5, high=5)
            print(out4)
            print(out4.dtype)
            # [[0, -3]]  # random
            # paddle.int32

            # example 5:
            # dtype is None and the dtype of x is int64
            x = paddle.zeros((1,2)).astype("int64")
            out5 = paddle.randint_like(x, low=-5, high=5)
            print(out5)
            print(out5.dtype)
            # [[0, -3]]  # random
            # paddle.int64

            # example 6:
            # dtype is float64 and the dtype of x is float32
            x = paddle.zeros((1,2)).astype("float32")
            out6 = paddle.randint_like(x, low=-5, high=5, dtype="float64")
            print(out6)
            print(out6.dtype)
            # [[0, -1]]  # random
            # paddle.float64

            # example 7:
            # dtype is bool and the dtype of x is float32
            x = paddle.zeros((1,2)).astype("float32")
            out7 = paddle.randint_like(x, low=-5, high=5, dtype="bool")
            print(out7)
            print(out7.dtype)
            # [[0, -1]]  # random
            # paddle.bool

            # example 8:
            # dtype is int32 and the dtype of x is float32
            x = paddle.zeros((1,2)).astype("float32")
            out8 = paddle.randint_like(x, low=-5, high=5, dtype="int32")
            print(out8)
            print(out8.dtype)
            # [[0, -1]]  # random
            # paddle.int32

            # example 9:
            # dtype is int64 and the dtype of x is float32
            x = paddle.zeros((1,2)).astype("float32")
            out9 = paddle.randint_like(x, low=-5, high=5, dtype="int64")
            print(out9)
            print(out9.dtype)
            # [[0, -1]]  # random
            # paddle.int64

            # example 10:
            # dtype is int64 and the dtype of x is bool
            x = paddle.zeros((1,2)).astype("bool")
            out10 = paddle.randint_like(x, low=-5, high=5, dtype="int64")
            print(out10)
            print(out10.dtype)
            # [[0, -1]]  # random
            # paddle.int64

    """
    if high is None:
        if low <= 0:
            raise ValueError(
                "If high is None, low must be greater than 0, but received low = {0}.".format(
                    low
                )
            )
        high = low
        low = 0
    if dtype is None:
        dtype = x.dtype
    if not isinstance(dtype, core.VarDesc.VarType):
        dtype = convert_np_dtype_to_dtype_(dtype)
    shape = paddle.shape(x)

    if low >= high:
        raise ValueError(
            "randint_like's low must less then high, but received low = {0}, "
            "high = {1}".format(low, high)
        )

    if paddle.in_dynamic_mode():
        shape = utils.convert_shape_to_list(shape)
        out = _legacy_C_ops.randint(
            'shape',
            shape,
            'low',
            low,
            'high',
            high,
            'seed',
            0,
            'dtype',
            core.VarDesc.VarType.INT64,
        )
        out = paddle.cast(out, dtype)
        return out

    check_shape(shape, 'randint_like')
    check_dtype(
        dtype,
        'dtype',
        ['bool', 'float16', 'float32', 'float64', 'int32', 'int64'],
        'randint_like',
    )

    inputs = {"ShapeTensor": shape}
    attrs = {
        'low': low,
        'high': high,
        'seed': 0,
        'dtype': core.VarDesc.VarType.INT64,
    }

    helper = LayerHelper("randint", **locals())
    out = helper.create_variable_for_type_inference(
        dtype=core.VarDesc.VarType.INT64
    )
    helper.append_op(
        type='randint', inputs=inputs, outputs={'Out': out}, attrs=attrs
    )
    out.stop_gradient = True
    out = paddle.cast(out, dtype)
    return out


def randperm(n, dtype="int64", name=None):
    """
    Returns a 1-D Tensor filled with random permutation values from 0
    to n-1, with ``dtype``.

    Args:
        n (int): The upper bound (exclusive), and it should be greater than 0.
        dtype (str|np.dtype, optional): The data type of
            the output Tensor. Supported data types: int32, int64, float32,
            float64. Default is int64.
        name (str, optional): The default value is None. Normally there is no
            need for user to set this property. For more information, please
            refer to :ref:`api_guide_Name`.

    Returns:
        Tensor: A 1-D Tensor filled with random permutation values from 0
        to n-1, with ``dtype``.

    Examples:
        .. code-block:: python

            import paddle

            out1 = paddle.randperm(5)
            # [4, 1, 2, 3, 0]  # random

            out2 = paddle.randperm(7, 'int32')
            # [1, 6, 2, 0, 4, 3, 5]  # random

    """
    if not isinstance(dtype, core.VarDesc.VarType):
        dtype = convert_np_dtype_to_dtype_(dtype)

    if in_dygraph_mode():
        return _C_ops.randperm(n, dtype, _current_expected_place())
    if _in_legacy_dygraph():
        return _legacy_C_ops.randperm('n', n, 'seed', 0, 'dtype', dtype)

    if n < 1:
        raise ValueError("The input n should be greater than 0 in randperm op.")
    check_dtype(
        dtype, 'dtype', ['int64', 'int32', 'float32', 'float64'], 'randperm'
    )

    helper = LayerHelper("randperm", **locals())
    out = helper.create_variable_for_type_inference(dtype)
    attrs = {'n': n, 'dtype': dtype, 'seed': 0}
    helper.append_op(
        type='randperm', inputs={}, outputs={'Out': out}, attrs=attrs
    )
    out.stop_gradient = True
    return out


def rand(shape, dtype=None, name=None):
    """
    Returns a Tensor filled with random values sampled from a uniform
    distribution in the range [0, 1), with ``shape`` and ``dtype``.

    Args:
        shape (list|tuple|Tensor): The shape of the output Tensor. If ``shape``
            is a list or tuple, the elements of it should be integers or Tensors
            (with the shape [1], and the data type int32 or int64). If ``shape``
            is a Tensor, it should be a 1-D Tensor(with the data type int32 or
            int64).
        dtype (str|np.dtype, optional): The data type of the output Tensor.
            Supported data types: float32, float64.
            Default is None, use global default dtype (see ``get_default_dtype``
            for details).
        name (str, optional): The default value is None. Normally there is no
            need for user to set this property. For more information, please
            refer to :ref:`api_guide_Name`.

    Returns:
        Tensor: A Tensor filled with random values sampled from a uniform
        distribution in the range [0, 1), with ``shape`` and ``dtype``.

    Examples:
        .. code-block:: python

            import paddle

            # example 1: attr shape is a list which doesn't contain Tensor.
            out1 = paddle.rand(shape=[2, 3])
            # [[0.451152  , 0.55825245, 0.403311  ],  # random
            #  [0.22550228, 0.22106001, 0.7877319 ]]  # random

            # example 2: attr shape is a list which contains Tensor.
            dim1 = paddle.to_tensor([2], 'int64')
            dim2 = paddle.to_tensor([3], 'int32')
            out2 = paddle.rand(shape=[dim1, dim2, 2])
            # [[[0.8879919 , 0.25788337],  # random
            #   [0.28826773, 0.9712097 ],  # random
            #   [0.26438272, 0.01796806]],  # random
            #  [[0.33633623, 0.28654453],  # random
            #   [0.79109055, 0.7305809 ],  # random
            #   [0.870881  , 0.2984597 ]]]  # random

            # example 3: attr shape is a Tensor, the data type must be int64 or int32.
            shape_tensor = paddle.to_tensor([2, 3])
            out3 = paddle.rand(shape_tensor)
            # [[0.22920267, 0.841956  , 0.05981819],  # random
            #  [0.4836288 , 0.24573246, 0.7516129 ]]  # random

    """
    return uniform(shape, dtype, min=0.0, max=1.0, name=name)


def exponential_(x, lam=1.0, name=None):
    r"""
    This inplace OP fill input Tensor ``x`` with random number from a Exponential Distribution.

    ``lam`` is :math:`\lambda` parameter of Exponential Distribution.

    .. math::

        f(x) = \lambda e^{-\lambda x}

    Args:
        x(Tensor):  Input tensor. The data type should be float32, float64.
        lam(float, optional): :math:`\lambda` parameter of Exponential Distribution. Default, 1.0.
        name(str, optional): The default value is None. Normally there is no
            need for user to set this property. For more information, please
            refer to :ref:`api_guide_Name`.
    Returns:
        Tensor: Input Tensor ``x``.

    Examples:
        .. code-block:: python

            import paddle
            paddle.set_device('cpu')
            paddle.seed(100)

            x = paddle.empty([2,3])
            x.exponential_()
            # [[0.80643415, 0.23211166, 0.01169797],
            #  [0.72520673, 0.45208144, 0.30234432]]

    """
    if in_dygraph_mode():
        return _C_ops.exponential_(x, lam)
    elif paddle.in_dynamic_mode():
        return _legacy_C_ops.exponential_(x, "lambda", lam)

    check_variable_and_dtype(x, "x", ["float32", "float64"], "exponential")

    helper = LayerHelper("exponential", **locals())
    helper.append_op(
        type='exponential',
        inputs={"X": x},
        outputs={'Out': x},
        attrs={"lambda": lam},
    )
    return x
