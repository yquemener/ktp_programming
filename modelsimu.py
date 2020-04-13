import igraph as ig
import pandas as pd


class Model:
    def __init__(self):
        # name, value, color
        self.states = list()
        self.init_values = list()

        # src_id, dst_id, code, dependencies
        self.transitions = list()

        # list of transitions
        self.run_order = None
        self.log = list()
        self.parameters = dict()
        self.layout = list()

    def run(self, steps=60, pandas=False):
        self.init_values = [x[1] for x in self.states]
        self.log = list()
        for k in range(steps):
            sv, tv = self.run_once()
            self.log.append(sv + tv)
        for i, s in enumerate(self.states):
            s[1] = self.init_values[i]

        if pandas:
            labels = [x[0] for x in self.states]
            labels += [self.states[t[0]][0] + " to " + self.states[t[1]][0] for t in self.transitions]
            return pd.DataFrame(self.log, columns=labels)
        else:
            return self.log

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
                g.add_vertex(state[0], color=state[2],
                             label=state[0], shape="rect",
                             x=self.layout[i][0], y=self.layout[i][1])
            else:
                g.add_vertex(state[0], color=state[2], label=state[0], shape="rect")
        for transition in self.transitions:
            g.add_edge(transition[0], transition[1])
        return ig.plot(g, bbox=(200, 200))
