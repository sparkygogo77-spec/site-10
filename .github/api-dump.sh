CP="$1"
p() { echo "=================== $*"; javap -p -cp "$CP" "$@" 2>&1 | grep -v 'lambda\$'; }
c() { echo "=================== -c $*"; javap -p -c -cp "$CP" "$@" 2>&1; }
p net.minecraft.world.item.component.UseEffects
p net.minecraft.core.component.DataComponents
c net.minecraft.client.player.LocalPlayer
p net.minecraft.world.item.Item\$Properties
