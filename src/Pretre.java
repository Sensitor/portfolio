public class Pretre extends Profil {
    public Pretre() {
        super("Pretre", 8, 8);
        voies.add(new VoieGuerreSainte());
        voies.add(new VoieDeLaPriere());
        voies.add(new VoieDesSoins());
    }

    @Override
    public int getAttaqueMagique(int modInt, int modSag, int niv) {
        return modSag + 1 + niv;
    }
}
