public class Barbare extends Profil {
    public Barbare() {
        super("Barbare", 12, 12);
        voies.add(new VoieDuBouclier());
        voies.add(new VoieDuCombat());
        voies.add(new VoieDeLaResistance());
    }

    @Override
    public int getBonusAttaqueMelee(int niv) {
        return niv;
    }
}
