public class Magicien extends Profil {
    public Magicien() {
        super("Magicien", 4, 4);
        voies.add(new VoieMagieDestructrice());
        voies.add(new VoieMagieProtectrice());
        voies.add(new VoieMagieUniverselle());
    }

    @Override
    public int getAttaqueMagique(int modInt, int modSag, int niv) {
        return modInt + 1 + niv;
    }
}
