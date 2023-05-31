from multiprocessing import Process, Pipe

import dill
import secrets

from GF256 import GF256


class Affine:
    def __init__(self, m, k, seed=666, verbosity=False):
        self.m = int(m)
        self.n = int(m)
        self.k = int(k)
        self.seed = secrets.randbelow(seed)
        self.verbosity = verbosity
        self.children = None
        self.parentEnds = None
        self.childEnds = None

    def generator(self, m, n, k, endPoint):
        try:
            m = int(m)
            n = int(n)
            k = int(k)
        except ValueError as _:
            print("M, N, and K must be integers!")

        iters = 0
        while True:
            l = list()
            for i in range(m):
                l.append(list())
                for j in range(n):
                    l[-1].append(GF256().get())

            try:
                linv = GF256().find_inverse(l)
                # print("tried : ",linv)
                break
            except Exception as _:
                iters += 1
                if iters % 100000 == 0:
                    print(iters, "done")
                pass

        b = list()
        for i in range(m):
            b.append(GF256().get())

        ret = dict()
        ret['l'] = l
        ret['linv'] = linv
        ret['b'] = b

        endPoint.send(dill.dumps(ret))
        exit(0)

    def start_generators(self, n):
        """
        Use `n` subprocesses to generate a random affine function.
        """
        # if __name__ == 'Affine':
        self.children = list()
        self.parentEnds = list()
        self.childEnds = list()
        for c in range(n):
            parentEnd, childEnd = Pipe(duplex=True)
            p = Process(target=self.generator, args=(self.m, self.n, self.k, childEnd))
            self.children.append(p)
            self.parentEnds.append(parentEnd)
            self.childEnds.append(childEnd)
            p.start()
            if self.verbosity:
                print("L Worker started with PID :", p.pid)

    def retrieve(self):
        """
        Retrieves the affine function from the first worker found to have completed!
        """
        done = -1
        tries = 0
        while done == -1:
            for c in range(len(self.children)):
                if self.parentEnds[c].poll(timeout=1):
                    done = c
                    break
            tries += 1

        ret = dill.loads(self.parentEnds[done].recv())

        for c in self.children:
            c.terminate()

        return ret
