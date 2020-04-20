import igraph as ig
import pandas as pd
import copy
import matplotlib as plt


class Model:
    def __init__(self, name=None):
        # name, value, color
        self.name = name
        self.states = list()
        self.init_values = list()

        # src_id, dst_id, code, dependencies
        self.transitions = list()

        # list of transitions
        self.run_order = None
        self.log = list()
        self.parameters = dict()
        self.layout = list()

        self.callbacks = dict()

    def copy(self, newname=None):
        m = copy.deepcopy(self)
        m.name = newname
        return m

    def run(self, steps=60, pandas=False):
        self.init_values = [x[1] for x in self.states]
        self.log = list()
        for k in range(steps):
            sv, tv = self.run_once()
            callbacks = self.callbacks.get(k, None)
            if not isinstance(callbacks, list):
                callbacks = [callbacks]
            for callb in callbacks:
                if callb is not None:
                    callb(self)
            callbacks = self.callbacks.get(-1, None)
            if not isinstance(callbacks, list):
                callbacks = [callbacks]
            for callb in callbacks:
                if callb is not None:
                    callb(self)
            self.log.append(sv + tv)
        for i, s in enumerate(self.states):
            s[1] = self.init_values[i]

        if pandas:
            return self.pandas_log()
        return self

    def pandas_log(self):
        labels = [x[0] for x in self.states]
        labels += [self.states[t[0]][0] + " to " + self.states[t[1]][0] for t in self.transitions]
        return pd.DataFrame(self.log, columns=labels)

    def run_once(self):
        transitions_value = [0] * len(self.transitions)
        if self.run_order is not None:
            order = self.run_order
        else:
            order = list(range(len(self.transitions)))
        for transition_id in order:
            transition = self.transitions[transition_id]
            src, dst, code, deps = transition
            args = list()
            for d in deps:
                if isinstance(d, str):
                    args.append(self.parameters[d])
                else:
                    args.append(self.states[d][1])
            delta = code(*args)
            self.states[src][1] -= delta
            self.states[dst][1] += delta
            transitions_value[transition_id] = delta
        return [x[1] for x in self.states], transitions_value

    def summary(self):
        g = ig.Graph(directed=True)
        for i, state in enumerate(self.states):
            if i <len(self.layout):
                x = self.layout[i][0]
                y = self.layout[i][1]
                dist = orient = 0
                if len(self.layout[i])>2:
                    orient = self.layout[i][2]
                    dist=1
                g.add_vertex(state[0], color=state[2],
                             label=state[0], shape="circle",
                             x=x, y=y,
                             label_dist=dist,
                             label_degree=orient * 3.14159/2,
                             size=40
                )
            else:
                g.add_vertex(state[0],
                             color=state[2],
                             label=state[0],
                             shape="circle",
                             size=40)
        for transition in self.transitions:
            g.add_edge(transition[0], transition[1])
        return ig.plot(g, bbox=(500, 300), margin=70)


def plot_one(models, columns=None, ax=None, show_policies=False):
    legend = list()
    if ax is None:
        f, ax = plt.pyplot.subplots()
    for imod, model in enumerate(models):
        if model.name is not None:
            label_model = model.name
        else:
            label_model = f"m{imod}"
        if columns is None:
            model.pandas_log().plot(ax=ax)
        else:
            for col in columns:
                model.pandas_log()[col].plot(ax=ax)
                legend.append(f"{col}, {label_model}")

    if show_policies:
        dates = set()
        for m in models:
            dates = dates.union(set(m.callbacks.keys()))
        for d in dates:
            if d > 0:
                ax.axvline(x=d, color='black', linestyle="--")

    ax.legend(legend)
