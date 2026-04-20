"""
Mixin to auto-apply Tailwind CSS classes to all form widgets.
Import and use in form classes to keep templates clean.
"""
INPUT_CLASSES = "block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
SELECT_CLASSES = "block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none bg-white"
TEXTAREA_CLASSES = "block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
FILE_CLASSES = "block w-full text-sm text-gray-500 file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"


class TailwindFormMixin:
    """Mixin for Django ModelForms. Call apply_tailwind() in __init__."""

    def apply_tailwind(self):
        from django.forms import (
            TextInput, EmailInput, NumberInput, URLInput, PasswordInput,
            DateInput, DateTimeInput, TimeInput,
            Textarea, Select, CheckboxInput, FileInput, ClearableFileInput,
        )
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (TextInput, EmailInput, NumberInput, URLInput, PasswordInput, DateInput, DateTimeInput, TimeInput)):
                widget.attrs.setdefault("class", INPUT_CLASSES)
            elif isinstance(widget, Textarea):
                widget.attrs.setdefault("class", TEXTAREA_CLASSES)
            elif isinstance(widget, Select):
                widget.attrs.setdefault("class", SELECT_CLASSES)
            elif isinstance(widget, (FileInput, ClearableFileInput)):
                widget.attrs.setdefault("class", FILE_CLASSES)
