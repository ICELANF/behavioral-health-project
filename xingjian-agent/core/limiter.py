class EfficacyLimiter:
    """
    八爪鱼限幅引擎：根据用户效能感调节任务难度
    """
    @staticmethod
    def get_constraints(efficacy_score: int):
        # 核心逻辑：效能越低，任务越少，难度越小
        if efficacy_score < 20:
            return {"max_tasks": 1, "max_difficulty": 1}
        elif efficacy_score < 50:
            return {"max_tasks": 2, "max_difficulty": 2}
        else:
            return {"max_tasks": 3, "max_difficulty": 5}

    @staticmethod
    def clamp(raw_tasks, efficacy_score):
        constraints = EfficacyLimiter.get_constraints(efficacy_score)
        # 过滤掉超过难度的任务，并限制数量
        clamped = [t for t in raw_tasks if t['difficulty'] <= constraints['max_difficulty']]
        return clamped[:constraints['max_tasks']]
