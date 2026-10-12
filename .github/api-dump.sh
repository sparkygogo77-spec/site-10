CP="$1"
p() { echo "=================== $*"; javap -p -cp "$CP" "$@" 2>&1 | grep -v 'lambda\$'; }
c() { echo "=================== -c $*"; javap -p -c -cp "$CP" "$@" 2>&1; }
c net.minecraft.client.renderer.entity.player.AvatarRenderer
p net.minecraft.client.renderer.entity.LivingEntityRenderer
p net.minecraft.client.renderer.entity.state.AvatarRenderState
p net.minecraft.client.renderer.entity.state.HumanoidRenderState
p net.minecraft.client.renderer.entity.state.LivingEntityRenderState
p net.minecraft.client.renderer.entity.state.EntityRenderState
c net.minecraft.client.model.HumanoidModel
c net.minecraft.client.model.player.PlayerModel
p net.minecraft.client.model.geom.ModelPart
p net.minecraft.world.entity.Avatar
p net.minecraft.client.player.AbstractClientPlayer
p net.minecraft.client.renderer.entity.EntityRenderer
