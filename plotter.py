
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import

import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import numpy as np

alpha_r = [x * 0.25 for x in range(1, 5)]
beta_r = [x * 0.1 for x in range(1, 11)]
ans = [[7060, 6360, 6223, 5103, 4260, 4386, 5935, 4283, 4316, 4932], [7075, 6686, 5250, 5650, 5482, 4801, 5435, 5350, 5935, 4977], [13363, 9074, 7815, 6494, 6014, 6109, 6029, 5524, 6036, 6346], [9979, 7834, 6735, 6461, 5832, 6358, 6282, 5538, 5486, 5370]]
ans2 = [[9215, 6830, 5294, 8513, 5782, 7069, 4526, 4538, 4559, 5143], [7193, 5530, 4480, 6863, 4889, 5890, 4200, 4193, 4185, 4507], [5785, 6292, 4951, 4361, 5966, 4756, 5221, 5871, 4417, 4525], [5399, 5879, 4699, 4202, 5653, 4572, 5000, 5616, 4322, 4394], [5168, 5630, 4546, 4103, 5465, 4460, 4868, 5462, 4264, 4314], [7096, 5414, 5614, 4846, 5508, 5265, 4634, 5072, 5490, 4786], [6864, 5285, 5486, 4768, 5403, 5178, 4581, 5004, 5407, 4739], [12506, 8748, 7454, 6589, 6729, 5743, 5870, 5465, 6279, 5667], [12167, 8560, 7320, 6491, 6632, 5681, 5810, 5423, 6214, 5621], [11889, 8406, 7212, 6413, 6555, 5634, 5760, 5386, 6159, 5584]]
ans3 = [[5994, 9046, 6766, 4530, 4359, 4434, 4660, 5015, 5346, 5644], [4892, 7131, 5511, 3973, 3935, 3945, 4106, 4369, 4610, 4851], [6850, 4932, 6375, 4341, 4943, 6233, 3979, 3947, 4164, 4323], [5902, 5487, 4365, 5692, 4108, 4229, 4638, 5213, 6048, 4244], [4829, 5512, 5031, 4565, 4823, 4091, 4139, 4259, 4549, 5003], [6916, 6081, 5315, 4674, 5334, 4351, 4715, 5307, 4484, 4508], [7177, 5981, 5012, 5353, 5447, 4681, 5698, 4544, 4653, 5104], [7419, 6683, 5894, 5219, 5578, 5187, 4859, 5184, 4721, 4784], [10129, 7645, 6089, 6137, 5484, 5458, 5119, 6092, 5209, 5647], [11666, 8704, 7150, 6786, 6412, 6580, 5435, 6094, 5470, 6076]]
ans_ad = [[11061, 8203, 7071, 6457, 5857, 5600, 5016, 4933, 4869, 4534], [8806, 6672, 5834, 5344, 4895, 4705, 4281, 4228, 4184, 3934], [7311, 5709, 5218, 4869, 4552, 4293, 4095, 3936, 3843, 3736], [6268, 5021, 4703, 4413, 4062, 3902, 3904, 3650, 3598, 3631], [5768, 4740, 4319, 4111, 3841, 3783, 3704, 3552, 3489, 3394], [5683, 4795, 4483, 4285, 3984, 3880, 3823, 3715, 3672, 3659], [5598, 4731, 4449, 4177, 4048, 3947, 3897, 3790, 3757, 3768], [6403, 5446, 4827, 4394, 4250, 4221, 4203, 4062, 4038, 3949], [7255, 5970, 5234, 4821, 4611, 4450, 4496, 4271, 4347, 4246], [8271, 6196, 5448, 5031, 4753, 4666, 4459, 4466, 4465, 4423]]
ans_sum = np.array([np.array(x) for x in ans_ad]) + np.array([np.array(x) for x in ans3])
ans_sum = ans_sum / 2
alpha_r2 = [x * 0.1 for x in range(1, 11)]
beta_r2 = [x * 0.1 for x in range(1, 11)]
print('\t\t' + '\t'.join(str(x)[:3] for x in beta_r2))
for idx, line in enumerate(ans_sum):
    print(str(alpha_r2[idx])[:4] + '0'*(4 - len(str(alpha_r2[idx]))) + '\t' + '\t'.join([str(x) for x in line]))


fig = plt.figure()
ax = fig.gca(projection='3d')

# Make data.
X = beta_r2
Y = alpha_r2
X, Y = np.meshgrid(X, Y)
plt_ans = np.array([np.array(x) for x in ans_sum])
Z = plt_ans

# Plot the surface.
surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm,
                       linewidth=0, antialiased=False)

# Customize the z axis.
ax.set_zlim(3500, 10000)
ax.zaxis.set_major_locator(LinearLocator(10))
ax.zaxis.set_major_formatter(FormatStrFormatter('%.0f'))

ax.set_xlabel('limit of overflow')
ax.set_ylabel('page utilization factor')
ax.set_zlabel('reads and writes')

# Add a color bar which maps values to colors.
fig.colorbar(surf, shrink=0.8, aspect=9, pad=0.1)

plt.show()
plt.close()

plt.imshow(plt_ans, cmap='coolwarm', extent=[0, 1, 1, 0])
plt.title('heatmap')
plt.xlabel('beta')
plt.ylabel('alpha')
# fig.colorbar(ax, shrink=0.3, aspect=8)
plt.colorbar()
plt.show()