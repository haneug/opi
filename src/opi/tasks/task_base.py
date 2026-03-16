import shutil
import typing
from pathlib import Path
from typing import Any

from pydantic import model_validator, BaseModel, ConfigDict

from opi.core import Calculator
from opi.input import Input
from opi.input.blocks import Block
from opi.input.structures import Structure



class TaskParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


    def map_to_input(self, input_object: Input) -> Input:
        hints = typing.get_type_hints(self.__class__, include_extras=True)

        for field_name, field_type in hints.items():
            value = getattr(self, field_name)

            args = typing.get_args(field_type)
            metadata = args[1:]


            match metadata:
                case (validator, ):
                    input_object.add_simple_keywords(value)
                case (validator, key):
                    block_type = Block.get_subclass_by_name(validator)
                    block_class = block_type(**{key: value})

                    block_exists, *_ = input_object.has_blocks(block_type)
                    if not block_exists:
                        input_object.add_blocks(block_class)
                    else:
                        existing_block = next(iter(input_object.get_blocks(type(block_class)).values()))
                        new_block = block_type.model_validate({**existing_block.model_dump(), **block_class.model_dump(exclude_unset=True)})
                        input_object.add_blocks(new_block, overwrite=True)

        return input_object


    @model_validator(mode='before')
    @classmethod
    def validate(cls, data: dict) -> dict:
        hints = typing.get_type_hints(cls, include_extras=True)

        for field_name, hint in hints.items():
            value = data.get(field_name)
            print(f"{field_name}: {hint}")
            if field_name not in data:
                continue

            args = typing.get_args(hint)
            metadata = args[1:]

            match metadata:
                case (validator,):
                    keyword = validator.find_keyword(data[field_name])
                    data[field_name] = keyword

                case (validator, key):
                    block_cls = Block.get_subclass_by_name(validator)
                    instance = block_cls.model_validate({key: value})
                    data[field_name] = getattr(instance, key)


        return data



class Task(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    task_parameters: TaskParams
    input_object: Input | None = Input()

    def __init__(self, /, **data: Any):
        super().__init__(**data)


    def run(self, basename: str, struct: Structure, working_dir:Path | None = Path("RUN"), ncores:int | None = None, memory:int | None = None, moinp: Path | None = None) -> "TaskResults":

        # > recreate the working dir
        shutil.rmtree(working_dir, ignore_errors=True)
        working_dir.mkdir()

        if ncores:
            self.input_object.ncores = ncores

        if memory:
            self.input_object.memory = memory

        if moinp:
            self.input_object.moinp = moinp


        self.input_object = self.task_parameters.map_to_input(input_object=self.input_object)

        calc = Calculator(basename, working_dir=working_dir)
        calc.structure = struct
        calc.input = self.input_object

        calc.write_and_run()

        return TaskResults()


class TaskResults:
    pass






