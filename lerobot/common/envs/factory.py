from torchrl.envs import SerialEnv
from torchrl.envs.transforms import Compose, StepCounter, Transform, TransformedEnv


def make_env(cfg, transform=None):
    """
    Note: The returned environment is wrapped in a torchrl.SerialEnv with cfg.rollout_batch_size underlying
    environments. The env therefore returns batches.`
    """

    kwargs = {
        "frame_skip": cfg.env.action_repeat,
        "from_pixels": cfg.env.from_pixels,
        "pixels_only": cfg.env.pixels_only,
        "image_size": cfg.env.image_size,
        "seed": cfg.seed,
        "num_prev_obs": cfg.n_obs_steps - 1,
    }

    if cfg.env.name == "simxarm":
        from lerobot.common.envs.simxarm import SimxarmEnv

        kwargs["task"] = cfg.env.task
        clsfunc = SimxarmEnv
    elif cfg.env.name == "pusht":
        from lerobot.common.envs.pusht.env import PushtEnv

        # assert kwargs["seed"] > 200, "Seed 0-200 are used for the demonstration dataset, so we don't want to seed the eval env with this range."

        clsfunc = PushtEnv
    elif cfg.env.name == "aloha":
        from lerobot.common.envs.aloha.env import AlohaEnv

        kwargs["task"] = cfg.env.task
        clsfunc = AlohaEnv
    else:
        raise ValueError(cfg.env.name)

    def _make_env(seed):
        nonlocal kwargs
        kwargs["seed"] = seed
        env = clsfunc(**kwargs)

        # limit rollout to max_steps
        env = TransformedEnv(env, StepCounter(max_steps=cfg.env.episode_length))

        if transform is not None:
            # useful to add normalization
            if isinstance(transform, Compose):
                for tf in transform:
                    env.append_transform(tf.clone())
            elif isinstance(transform, Transform):
                env.append_transform(transform.clone())
            else:
                raise NotImplementedError()

        return env

    return SerialEnv(
        cfg.rollout_batch_size,
        create_env_fn=_make_env,
        create_env_kwargs={
            "seed": env_seed  # noqa: B035
            for env_seed in range(cfg.seed, cfg.seed + cfg.rollout_batch_size)
        },
    )


# def make_env(env_name, frame_skip, device, is_test=False):
#     env = GymEnv(
#         env_name,
#         frame_skip=frame_skip,
#         from_pixels=True,
#         pixels_only=False,
#         device=device,
#     )
#     env = TransformedEnv(env)
#     env.append_transform(NoopResetEnv(noops=30, random=True))
#     if not is_test:
#         env.append_transform(EndOfLifeTransform())
#         env.append_transform(RewardClipping(-1, 1))
#     env.append_transform(ToTensorImage())
#     env.append_transform(GrayScale())
#     env.append_transform(Resize(84, 84))
#     env.append_transform(CatFrames(N=4, dim=-3))
#     env.append_transform(RewardSum())
#     env.append_transform(StepCounter(max_steps=4500))
#     env.append_transform(DoubleToFloat())
#     env.append_transform(VecNorm(in_keys=["pixels"]))
#     return env
