from typing import TYPE_CHECKING, TypeVar, Generic, ClassVar, Literal, Annotated, Any, overload
from collections.abc import Callable

T = TypeVar("T")
TT = TypeVar("TT")
InstanceT = TypeVar("InstanceT")

if TYPE_CHECKING:
    from typing_extensions import Self


class InjectionError(Exception):
    def __init__(self, key: Any) -> None:
        super().__init__(f"'{key}' instance is inaccessible")


class DependencyInjector(Generic[T, InstanceT]):
    container: ClassVar[dict[str | type, Any]] = dict()
    factories: ClassVar[dict[str | type, Callable[[], Any]]] = dict()
    key: str | type[T]

    def __init__(self, key: str | type[T]) -> None:
        self.key = key

    @property
    def value(self) -> T:
        return self.get(self.key)

    @overload
    def __get__(self, instance: InstanceT, cls: type[InstanceT] | None = None) -> T:
        ...

    @overload
    def __get__(self, instance: Literal[None], cls: type[InstanceT]) -> "Self":
        ...

    def __get__(
        self,
        instance: InstanceT | None,
        cls: type[InstanceT] | None = None
    ) -> "T | Self":
        if instance is None:
            return self
        return self.value

    @classmethod
    def store(cls, value: Annotated[TT, "SameAs[T]"], key: str | type[TT] | None = None) -> TT:
        if key is None:
            key = type(value)
        cls.container[key] = value
        return value

    @overload
    @classmethod
    def register_factory(
        cls,
        factory: Callable[[], Annotated[TT, "SameAs[T]"]],
        *,
        key: str | type[TT]
    ):
        ...

    @overload
    @classmethod
    def register_factory(
        cls,
        factory: type[Annotated[TT, "SameAs[T]"]],
        *,
        key: str | type[TT] | None = None
    ):
        ...

    @classmethod
    def register_factory(
        cls,
        factory: Callable[[], Annotated[TT, "SameAs[T]"]],
        *,
        key: str | type[TT] | None = None
    ):
        if key is None:
            if isinstance(factory, type):
                key = factory
            else:
                raise Exception("invalid key")
        cls.factories[key] = factory

    @classmethod
    def get(cls, key: str | type[Annotated[TT, "SameAs[T]"]]) -> TT:
        value = cls.container.get(key)
        if value is None:
            factory = cls.factories.get(key)
            if factory is not None:
                value = factory()
                cls.container[key] = value

        if value is None:
            raise InjectionError(key)
        else:
            return value
