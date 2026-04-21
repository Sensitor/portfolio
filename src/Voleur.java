public class Voleur extends Profil {
    public Voleur() {
        super("Voleur", 6, 6);
        voies.add(new VoieDeLAssassin());
        voies.add(new VoieDuDeplacement());
        voies.add(new VoieDuRoublard());
    }

    @Override
    public int getBonusAttaqueDistance(int niv) {
        return niv;
    }
}
