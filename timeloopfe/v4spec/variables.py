from ..parsing.nodes import DictNode


class Variables(DictNode):
    @classmethod
    def init_elems(cls, *args, **kwargs):
        super().init_elems(*args, **kwargs)
        cls.recognize_all()


Variables.init_elems()
