from rest_framework import serializers
from .models import Hardware, UserHardware


class HardwareSerializer(serializers.ModelSerializer):
    is_owned = serializers.SerializerMethodField()
    is_interested = serializers.SerializerMethodField()

    class Meta:
        model = Hardware
        fields = [
            'id', 'name', 'category', 'manufacturer',
            'price', 'original_price', 'discount_percent',
            'image_url', 'specs', 'benchmark_score', 'created_at',
            'is_owned', 'is_interested',
        ]

    def get_is_owned(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user_hardware.filter(user=request.user, status='owned').exists()
        return False

    def get_is_interested(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user_hardware.filter(user=request.user, status='interested').exists()
        return False


class UserHardwareSerializer(serializers.ModelSerializer):
    hardware = HardwareSerializer(read_only=True)
    hardware_id = serializers.PrimaryKeyRelatedField(
        queryset=Hardware.objects.all(), source='hardware', write_only=True
    )

    class Meta:
        model = UserHardware
        fields = ['id', 'hardware', 'hardware_id', 'status', 'added_at']
