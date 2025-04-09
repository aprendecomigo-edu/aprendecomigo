from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """
    Base serializer with common functionality.
    """

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_fields(self):
        """
        Modify fields based on request method (GET, POST, PUT, PATCH)
        """
        fields = super().get_fields()
        request = self.context.get("request", None)
        if request and request.method == "GET":
            # For example, you can add additional fields for GET requests
            pass
        return fields


class BaseNestedModelSerializer(BaseSerializer):
    """
    Base serializer for handling nested serializations consistently.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'depth' arg up to the superclass
        depth = kwargs.pop("depth", 0)
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)
        if hasattr(self, "Meta"):
            self.Meta.depth = depth

    def to_representation(self, instance):
        """
        Custom representation that handles nested objects
        """
        ret = super().to_representation(instance)
        return ret


class ReadWriteSerializerMethodField(serializers.SerializerMethodField):
    """
    Serializer method field that can be used for both read and write operations.
    """

    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs["source"] = "*"
        super(serializers.SerializerMethodField, self).__init__(**kwargs)
